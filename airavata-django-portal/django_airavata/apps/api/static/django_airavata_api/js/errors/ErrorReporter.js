import { services } from "..";
import LogRecord from "../models/LogRecord";

class ErrorReporter {
  reportUnhandledError(unhandledError) {
    console.log(JSON.stringify(unhandledError, null, 4));

    const stacktrace = (unhandledError.error?.stack || "")
      .split("\n")
      .map((frame) => frame.trim())
      .filter((frame) => frame.length > 0);
    services.LoggingService.send(
      {
        data: new LogRecord({
          level: "ERROR",
          message: unhandledError.message,
          details: unhandledError.details,
          stacktrace: stacktrace,
        }),
      },
      { ignoreErrors: true },
    ).catch((err) => {
      console.log("Failed to log error", err);
    });
  }
}

export default new ErrorReporter();
