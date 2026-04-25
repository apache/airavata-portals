import { describe, expect, it, vi } from "vitest";
import { useConfirmReset } from "../../../js/composables/useConfirmReset";

describe("useConfirmReset", () => {
  it("calls onConfirm when window.confirm returns true", () => {
    vi.spyOn(window, "confirm").mockReturnValueOnce(true);
    const fn = vi.fn();
    const guarded = useConfirmReset("ok?", fn);
    guarded();
    expect(fn).toHaveBeenCalledTimes(1);
  });

  it("skips onConfirm when window.confirm returns false", () => {
    vi.spyOn(window, "confirm").mockReturnValueOnce(false);
    const fn = vi.fn();
    useConfirmReset("ok?", fn)();
    expect(fn).not.toHaveBeenCalled();
  });
});
