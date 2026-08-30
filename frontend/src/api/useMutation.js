import { useCallback, useRef, useState } from "react";

/**
 * Runs a write — save, delete, publish — and tracks the three things
 * every one of them needs: whether it is in flight, what went wrong, and
 * not letting it fire twice.
 *
 *     const save = useMutation(() => courseBuilderApi.update(id, payload), {
 *       onSuccess: onSaved,
 *     });
 *
 *     <Button onClick={save.run} disabled={save.busy}>
 *       {save.busy ? "Saving" : "Save"}
 *     </Button>
 *     {save.error && <div className="form-error">{save.error.message}</div>}
 *
 * Every page was writing this by hand, and most of them got the same
 * detail wrong: `setBusy(false)` in the success path as well as the
 * failure path, so a slow save could be submitted twice.
 *
 * `busy` deliberately stays true after a successful run when `onSuccess`
 * unmounts the component — releasing it there would set state on
 * something that no longer exists.
 */
export function useMutation(action, { onSuccess } = {}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const inFlight = useRef(false);

  const run = useCallback(
    async (...args) => {
      // Guards the double-click, which state alone cannot: two clicks in
      // the same tick both see the old `busy`.
      if (inFlight.current) return undefined;
      inFlight.current = true;

      setBusy(true);
      setError(null);

      try {
        const result = await action(...args);
        inFlight.current = false;
        if (onSuccess) onSuccess(result);
        return result;
      } catch (caught) {
        inFlight.current = false;
        setBusy(false);
        setError(caught);
        return undefined;
      }
    },
    [action, onSuccess]
  );

  const reset = useCallback(() => {
    setBusy(false);
    setError(null);
    inFlight.current = false;
  }, []);

  return { run, busy, error, reset };
}
