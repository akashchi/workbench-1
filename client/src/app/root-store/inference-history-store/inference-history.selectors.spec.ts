/* eslint-disable quote-props */
import { Dictionary } from '@ngrx/entity';
import { keys, values } from 'lodash';

import { THROUGHPUT_UNIT } from '@store/model-store/model.model';

import { DeviceTargets } from '@shared/models/device';

import {
  selectAllInferenceItems,
  selectHiddenInferenceItems,
  selectInferenceError,
  selectInferenceIsLoading,
  selectSelectedInferencePoint,
} from './inference-history.selectors';
import { IInferenceResult } from './inference-history.model';
import { ProjectStatus, ProjectStatusNames } from '../project-store/project.model';
import { initialState, State as InferenceHistoryState } from './inference-history.state';
import { State as AppState } from '../state';

const createInferenceItemStatus = ({
  status = {
    errorMessage: 'Error message',
    name: ProjectStatusNames.READY,
    progress: 100,
  },
} = {}) => ({ ...status } as ProjectStatus);

const mockInferenceItemsMap: Dictionary<IInferenceResult> = {
  '1': {
    id: 1,
    projectId: 1,
    profilingJobId: 1,
    status: createInferenceItemStatus(),
    deviceType: DeviceTargets.CPU,
    created: Date.now(),
    updated: Date.now(),
    started: Date.now(),
    batch: 1,
    nireq: 1,
    isAutoBenchmark: false,
    autogenerated: false,
    latency: 10,
    throughput: 10,
    throughputUnit: THROUGHPUT_UNIT.FPS,
    totalExecutionTime: 10,
    inferenceTime: 20,
  },
  '2': {
    id: 2,
    projectId: 1,
    profilingJobId: 2,
    status: createInferenceItemStatus(),
    deviceType: DeviceTargets.CPU,
    created: Date.now(),
    updated: Date.now(),
    started: Date.now(),
    batch: 1,
    nireq: 1,
    isAutoBenchmark: false,
    autogenerated: false,
    latency: 20,
    throughput: 10,
    throughputUnit: THROUGHPUT_UNIT.FPS,
    totalExecutionTime: 10,
    inferenceTime: 20,
  },
  '3': {
    id: 3,
    projectId: 1,
    profilingJobId: 2,
    status: createInferenceItemStatus(),
    deviceType: DeviceTargets.CPU,
    created: Date.now(),
    updated: Date.now(),
    started: Date.now(),
    batch: 1,
    nireq: 2,
    isAutoBenchmark: false,
    autogenerated: false,
    latency: 30,
    throughput: 10,
    throughputUnit: THROUGHPUT_UNIT.FPS,
    totalExecutionTime: 10,
    inferenceTime: 20,
  },
};

const createState = (): InferenceHistoryState => ({
  ...initialState,
  entities: mockInferenceItemsMap,
  ids: keys(mockInferenceItemsMap),
});

describe('Inference History Selectors', () => {
  let state: InferenceHistoryState;

  beforeAll(() => {
    state = createState();
  });

  describe('selectInferenceError', () => {
    it('should return error', () => {
      const result = selectInferenceError.projector(state);
      expect(result).toEqual(state.error);
    });
  });

  describe('selectInferenceIsLoading', () => {
    it('should return loading status', () => {
      const result = selectInferenceIsLoading.projector(state);
      expect(result).toEqual(state.isLoading);
    });
  });

  describe('selectSelectedInferencePoint', () => {
    it('should return selected inference point', () => {
      const result = selectSelectedInferencePoint.projector(state);
      expect(result).toEqual(state.selectedId);
    });
  });

  describe('selectFilteredInferenceItems', () => {
    it('should return array of inference points for comparison', () => {
      const result = selectHiddenInferenceItems.projector(state);
      expect(result).toBeArray();
      expect(result).toEqual(state.hiddenIds);
    });
  });

  describe('selectAllInferenceItems', () => {
    it('should return array of inference items', () => {
      const result = selectAllInferenceItems({ inferenceHistory: state } as AppState);
      expect(result).toBeArray();
      expect(result).toEqual(values(state.entities));
    });
  });
});
