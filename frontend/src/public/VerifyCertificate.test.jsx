import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import VerifyCertificate from "./VerifyCertificate";
import { certificateApi } from "../api/endpoints";
import { renderAt } from "../test/render";

vi.mock("../api/endpoints", () => ({
  certificateApi: { verify: vi.fn() },
}));

const CERTIFICATE = {
  certificate_number: "ARNAV-A1B2C3D4E5F60718",
  holder_name: "Ada Lovelace",
  course_title: "Fire Safety",
  issued_at: "2026-03-14T10:30:00+00:00",
};

function notFound() {
  return Object.assign(new Error("No certificate found with that number"), {
    status: 404,
    isNotFound: true,
  });
}

beforeEach(() => {
  certificateApi.verify.mockReset();
});

describe("a number in the URL", () => {
  it("is checked straight away", async () => {
    certificateApi.verify.mockResolvedValue(CERTIFICATE);

    renderAt(<VerifyCertificate />, {
      path: "/verify/:certificateNumber",
      at: `/verify/${CERTIFICATE.certificate_number}`,
    });

    expect(
      await screen.findByText("This certificate is genuine.")
    ).toBeInTheDocument();
    expect(screen.getByText("Ada Lovelace")).toBeInTheDocument();
    expect(screen.getByText("Fire Safety")).toBeInTheDocument();
  });

  it("says so when it does not match", async () => {
    certificateApi.verify.mockRejectedValue(notFound());

    renderAt(<VerifyCertificate />, {
      path: "/verify/:certificateNumber",
      at: "/verify/ARNAV-NOPE",
    });

    expect(
      await screen.findByText("No certificate matches that number.")
    ).toBeInTheDocument();
  });

  it("shows the date it was issued", async () => {
    certificateApi.verify.mockResolvedValue(CERTIFICATE);

    renderAt(<VerifyCertificate />, {
      path: "/verify/:certificateNumber",
      at: `/verify/${CERTIFICATE.certificate_number}`,
    });

    expect(await screen.findByText(/14 March 2026/)).toBeInTheDocument();
  });
});

describe("typing a number in", () => {
  it("checks it and reports a match", async () => {
    const user = userEvent.setup();
    certificateApi.verify.mockResolvedValue(CERTIFICATE);

    renderAt(<VerifyCertificate />, { path: "/verify", at: "/verify" });

    await user.type(
      screen.getByLabelText("Certificate number"),
      CERTIFICATE.certificate_number
    );
    await user.click(screen.getByRole("button", { name: "Check certificate" }));

    expect(
      await screen.findByText("This certificate is genuine.")
    ).toBeInTheDocument();
    expect(certificateApi.verify).toHaveBeenCalledWith(
      CERTIFICATE.certificate_number
    );
  });

  it("reports a number that does not match", async () => {
    const user = userEvent.setup();
    certificateApi.verify.mockRejectedValue(notFound());

    renderAt(<VerifyCertificate />, { path: "/verify", at: "/verify" });

    await user.type(screen.getByLabelText("Certificate number"), "ARNAV-NOPE");
    await user.click(screen.getByRole("button", { name: "Check certificate" }));

    expect(
      await screen.findByText("No certificate matches that number.")
    ).toBeInTheDocument();
  });

  it("cannot be submitted empty", async () => {
    renderAt(<VerifyCertificate />, { path: "/verify", at: "/verify" });

    expect(
      screen.getByRole("button", { name: "Check certificate" })
    ).toBeDisabled();
  });

  it("clears a previous answer when the number is edited", async () => {
    const user = userEvent.setup();
    certificateApi.verify.mockResolvedValue(CERTIFICATE);

    renderAt(<VerifyCertificate />, { path: "/verify", at: "/verify" });

    const input = screen.getByLabelText("Certificate number");
    await user.type(input, CERTIFICATE.certificate_number);
    await user.click(screen.getByRole("button", { name: "Check certificate" }));
    await screen.findByText("This certificate is genuine.");

    await user.type(input, "X");

    await waitFor(() =>
      expect(screen.queryByText("This certificate is genuine.")).toBeNull()
    );
  });
});

describe("what it does not show", () => {
  it("never renders anything the API did not return", async () => {
    // The endpoint is unauthenticated, so it carries only the holder's
    // name, the course and the date. Nothing here should invent more.
    certificateApi.verify.mockResolvedValue(CERTIFICATE);

    const { container } = renderAt(<VerifyCertificate />, {
      path: "/verify/:certificateNumber",
      at: `/verify/${CERTIFICATE.certificate_number}`,
    });

    await screen.findByText("This certificate is genuine.");

    expect(container.textContent).not.toMatch(/@/);
    expect(container.textContent).not.toMatch(/department/i);
    expect(container.textContent).not.toMatch(/score/i);
  });
});
