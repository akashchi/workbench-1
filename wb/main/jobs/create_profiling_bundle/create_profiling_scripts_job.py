"""
 OpenVINO DL Workbench
 Class for create profiling scripts job

 Copyright (c) 2021 Intel Corporation

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at
      http://www.apache.org/licenses/LICENSE-2.0
 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
"""
from contextlib import closing
from functools import partial
from shutil import rmtree
from typing import List, Tuple, Dict

import numpy as np
from sqlalchemy.orm import Session

from wb.extensions_factories.database import get_db_session_for_celery
from wb.main.dataset_utils.dataset_adapters import BaseTextDatasetAdapter
from wb.main.enumerates import JobTypesEnum, StatusEnum
from wb.main.jobs.interfaces.ijob import IJob
from wb.main.models import ProfilingJobModel, CreateProfilingScriptsJobModel, DatasetsModel, SingleInferenceInfoModel
from wb.main.scripts.job_scripts_generators import get_profiling_job_script_generator
from wb.main.scripts.job_scripts_generators.profiling_configuration_generator import \
    get_profiling_configuration_generator, ProfilingInputFileMapping
from wb.main.utils.tokenizer.tokeinzer_wrapper import TokenizerWrapper
from wb.main.utils.utils import create_empty_dir


# TODO Consider renaming to `CreateProfilingAssetsJob`
class CreateProfilingScriptsJob(IJob):
    job_type = JobTypesEnum.create_profiling_scripts_type
    _job_model_class = CreateProfilingScriptsJobModel

    def __init__(self, job_id: int, **unused_kwargs):
        super().__init__(job_id=job_id)
        self._attach_default_db_and_socket_observers()

    def run(self):
        self._job_state_subject.update_state(status=StatusEnum.running, progress=0, log='Creating profiling bundle.')
        with closing(get_db_session_for_celery()) as session:
            session: Session
            job_model = self.get_job_model(session)
            pipeline_id = job_model.pipeline_id
            profiling_job: ProfilingJobModel = session.query(ProfilingJobModel) \
                .filter_by(pipeline_id=pipeline_id).first()

            create_empty_dir(profiling_job.profiling_scripts_dir_path)

            profiling_input_file_mapping = None
            if not profiling_job.autogenerated:
                profiling_input_file_mapping = self._generate_profiling_input_binary_data(
                    profiling_job_model=profiling_job)

            profiling_configuration_generator = get_profiling_configuration_generator(
                profiling_job=profiling_job,
                profiling_input_file_mapping=profiling_input_file_mapping)
            profiling_configuration_generator.generate()

            job_script_generator = get_profiling_job_script_generator(profiling_job=profiling_job)
            job_script_generator.create(result_file_path=str(profiling_job.profiling_job_script_path))

        self.on_success()

    def on_success(self):
        self._job_state_subject.update_state(status=StatusEnum.ready,
                                             log='Profiling bundle creation successfully finished.')
        self._job_state_subject.detach_all_observers()

    # TODO Consider moving to profiling utils
    def _generate_profiling_input_binary_data(self, profiling_job_model: ProfilingJobModel) \
            -> ProfilingInputFileMapping:
        binary_dataset_directory_path = profiling_job_model.binary_dataset_directory_path
        if binary_dataset_directory_path.exists():
            rmtree(binary_dataset_directory_path)
        binary_dataset_directory_path.mkdir()

        tokenizer = TokenizerWrapper.from_model(profiling_job_model.project.topology.tokenizer_model)
        dataset = profiling_job_model.project.dataset

        number_of_generated_inputs = self._get_number_of_generated_inputs(
            dataset=dataset,
            inferences=profiling_job_model.profiling_results
        )
        text_dataset_adapter = BaseTextDatasetAdapter.from_model(dataset, number_of_rows=number_of_generated_inputs)

        shapes, data_types = self._get_network_inputs(xml_model_path=profiling_job_model.xml_model_path)
        tokenizer = partial(
            tokenizer, **tokenizer.tokenizer_kwargs_from_model_shape(shapes)
        )

        profiling_input_file_mapping = ProfilingInputFileMapping()

        for idx, texts in zip(range(number_of_generated_inputs), text_dataset_adapter.feature_iter()):
            tokenized_text = tokenizer(texts)
            for (input_name, input_data), data_type in zip(tokenized_text.items(), data_types):
                file_path = binary_dataset_directory_path / f'{input_name}_{idx:03d}.bin'
                with file_path.open('w') as file:
                    input_data.astype(data_type).tofile(file)
                profiling_input_file_mapping.add_input_file(input_name=input_name, file_path=str(file_path))

        return profiling_input_file_mapping

    @staticmethod
    def _get_number_of_generated_inputs(dataset: DatasetsModel,
                                        inferences: List[SingleInferenceInfoModel]) -> int:
        number_of_generated_inputs = max(inference.batch * inference.nireq for inference in inferences)
        return min(number_of_generated_inputs, max(dataset.number_images, 1))

    @staticmethod
    def _get_network_inputs(xml_model_path: str) -> Tuple[Dict[str, List[int]], List]:
        from openvino.runtime import Core
        from openvino._pyopenvino import Model

        datatype_map = {
            'i32': np.int32,
            'i64': np.int64,
        }

        model: Model = Core().read_model(xml_model_path)
        shapes = {
            parameter.any_name: [
                *map(
                    lambda dimension: int(str(dimension)),
                    parameter.get_partial_shape()
                )
            ]
            for parameter in model.inputs
        }
        data_types = [datatype_map[parameter.get_element_type().get_type_name()] for parameter in model.inputs]

        return shapes, data_types
