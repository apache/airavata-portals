export default class OutputViewDataLoader {
  url: string | null;
  experimentId: string | null;
  experimentOutputName: string | null;
  providerId: string | null;
  data: Record<string, unknown> | null;

  constructor(opts: {
    url: string | null;
    experimentId: string | null;
    experimentOutputName: string | null;
    providerId: string | null;
  });

  load(newParams?: Record<string, unknown> | null): Promise<Record<string, unknown>>;
  createInteractiveParams(): Record<string, unknown>;
}
