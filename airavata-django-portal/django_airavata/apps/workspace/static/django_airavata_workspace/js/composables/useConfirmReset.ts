export function useConfirmReset<TArgs extends unknown[]>(message: string, fn: (...a: TArgs) => void) {
  return (...args: TArgs) => {
    if (window.confirm(message)) fn(...args);
  };
}
