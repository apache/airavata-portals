/**
 * Type definitions for experiment-related Pinia stores.
 * Derived from the Vuex modules in:
 *   - apps/workspace/static/.../store/modules/view-experiment.js
 *   - apps/workspace/static/.../web-components/store.js
 *
 * These are intentionally minimal — the full model shapes come from
 * django-airavata-api models. Here we only capture the "state slot" shapes
 * used directly in the store ref declarations.
 */

// ---------------------------------------------------------------------------
// Shared primitives
// ---------------------------------------------------------------------------

/** A sparse record mapping output names to the timestamp when an intermediate
 *  output fetch was requested. */
export type RunningIntermediateOutputFetches = Record<string, Date>;

// ---------------------------------------------------------------------------
// view-experiment store (experiment.ts)
// ---------------------------------------------------------------------------

/** Opaque model objects — typed as `unknown` here so that the stores compile
 *  without importing the full API model tree. Consumers that need the full
 *  shape should import the real model class from django-airavata-api. */
export type FullExperiment = Record<string, unknown>;
export type ApplicationInterface = Record<string, unknown>;
export type GroupResourceProfile = Record<string, unknown>;

// ---------------------------------------------------------------------------
// web-components store (webComponents.ts)
// ---------------------------------------------------------------------------

export type Experiment = Record<string, unknown>;
export type WorkspacePreferences = Record<string, unknown>;
export type ApplicationDeployment = Record<string, unknown>;
export type AppDeploymentQueue = Record<string, unknown>;
