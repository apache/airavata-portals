/**
 * Tracks the experiment currently being created/edited/viewed so that errors
 * reported while setting up an experiment can be associated with it, even when
 * the failing request URL/body doesn't itself contain the experiment id (e.g.
 * a group-resource-profile authorization error during setup).
 *
 * Components that own an experiment context should call setExperimentId on
 * mount and clearExperimentId on destroy.
 */
class ErrorContext {
  constructor() {
    this.experimentId = null;
  }

  setExperimentId(experimentId) {
    this.experimentId = experimentId || null;
  }

  clearExperimentId() {
    this.experimentId = null;
  }
}

export default new ErrorContext();
