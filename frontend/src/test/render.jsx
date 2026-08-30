import { render } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";

/**
 * Renders a component inside a router, at a chosen URL, with a route
 * pattern so `useParams` resolves.
 *
 *     renderAt(<QuizTake />, { path: "/quizzes/:quizId", at: "/quizzes/7" })
 *
 * Anything the component navigates to lands on the catch-all route, which
 * records where it went. Several of these flows are defined mostly by
 * where they send the student next — a passing quiz belongs back in the
 * course, not on the quiz list — so the destination is the thing worth
 * asserting on, rather than that some mocked `navigate` was called.
 */
export function renderAt(element, { path = "/", at = "/", state } = {}) {
  const destination = { pathname: at, state };

  function Destination() {
    const location = useLocation();
    destination.pathname = location.pathname;
    destination.state = location.state;
    return <div data-testid="navigated-to">{location.pathname}</div>;
  }

  const result = render(
    <MemoryRouter
      initialEntries={[{ pathname: at, state }]}
      // Opting in early keeps v7's deprecation warnings out of the test
      // output; the behaviour they describe is what we already rely on.
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
    >
      <Routes>
        <Route path={path} element={element} />
        <Route path="*" element={<Destination />} />
      </Routes>
    </MemoryRouter>
  );

  return {
    ...result,
    navigatedTo: () => destination.pathname,
    navigatedState: () => destination.state,
  };
}
