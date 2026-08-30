import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { useMutation } from "./useMutation";

function Harness({ action, onSuccess }) {
  const save = useMutation(action, { onSuccess });

  return (
    <div>
      <button onClick={save.run} disabled={save.busy}>
        {save.busy ? "Saving" : "Save"}
      </button>
      {save.error && <div data-testid="error">{save.error.message}</div>}
      <button onClick={save.reset}>reset</button>
    </div>
  );
}

describe("useMutation", () => {
  it("runs the action and reports success", async () => {
    const user = userEvent.setup();
    const action = vi.fn().mockResolvedValue({ id: 1 });
    const onSuccess = vi.fn();

    render(<Harness action={action} onSuccess={onSuccess} />);
    await user.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => expect(onSuccess).toHaveBeenCalledWith({ id: 1 }));
  });

  it("surfaces the error and stops being busy", async () => {
    const user = userEvent.setup();
    const action = vi.fn().mockRejectedValue(new Error("Username already taken"));

    render(<Harness action={action} />);
    await user.click(screen.getByRole("button", { name: "Save" }));

    expect(await screen.findByTestId("error")).toHaveTextContent(
      "Username already taken"
    );
    expect(screen.getByRole("button", { name: "Save" })).toBeEnabled();
  });

  it("does not call onSuccess when the action fails", async () => {
    const user = userEvent.setup();
    const onSuccess = vi.fn();

    render(
      <Harness action={vi.fn().mockRejectedValue(new Error("no"))} onSuccess={onSuccess} />
    );
    await user.click(screen.getByRole("button", { name: "Save" }));

    await screen.findByTestId("error");
    expect(onSuccess).not.toHaveBeenCalled();
  });

  it("ignores a second click while the first is still running", async () => {
    // The bug this exists to prevent: a slow save submitted twice, which
    // on the course builder meant two courses.
    const user = userEvent.setup();
    let release;
    const action = vi.fn(
      () => new Promise((resolve) => (release = () => resolve("done")))
    );

    render(<Harness action={action} />);

    const button = screen.getByRole("button", { name: "Save" });
    await user.click(button);
    await user.click(screen.getByRole("button", { name: "Saving" }));

    expect(action).toHaveBeenCalledTimes(1);
    release();
  });

  it("clears a previous error on the next attempt", async () => {
    const user = userEvent.setup();
    const action = vi
      .fn()
      .mockRejectedValueOnce(new Error("first failure"))
      .mockResolvedValue("ok");

    render(<Harness action={action} />);

    await user.click(screen.getByRole("button", { name: "Save" }));
    await screen.findByTestId("error");

    await user.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => expect(screen.queryByTestId("error")).toBeNull());
  });

  it("reset clears the error", async () => {
    const user = userEvent.setup();

    render(<Harness action={vi.fn().mockRejectedValue(new Error("nope"))} />);

    await user.click(screen.getByRole("button", { name: "Save" }));
    await screen.findByTestId("error");

    await user.click(screen.getByRole("button", { name: "reset" }));

    expect(screen.queryByTestId("error")).toBeNull();
  });
});
