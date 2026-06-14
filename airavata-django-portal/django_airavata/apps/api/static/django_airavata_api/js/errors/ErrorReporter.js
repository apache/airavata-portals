import { services } from "..";
import LogRecord from "../models/LogRecord";

import StackTrace from "stacktrace-js";

class ErrorReporter {
  reportUnhandledError(unhandledError) {
    console.log(JSON.stringify(unhandledError, null, 4));

    StackTrace.fromError(unhandledError.error)
      .then((stackframes) => {
        const stacktrace = stackframes.map((sf) => sf.toString());
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
      })
      .catch((err) => {
        console.log("Failed to produce stacktrace", err);
      });
  }
}

export default new ErrorReporter();
