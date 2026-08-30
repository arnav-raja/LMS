import { Component } from "react";

/**
 * Catches a render-time crash and shows something a person can act on.
 *
 * Without it, one thrown error in one component unmounts the entire React
 * tree and the user is left staring at a blank white page with no way
 * forward — not even the sidebar to navigate away with.
 *
 * Has to be a class: there is still no hook equivalent of
 * componentDidCatch.
 */
export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    // Kept to the console for now. Phase 8 routes this to a real error
    // tracker; until then this is the only record that it happened.
    console.error("Unhandled UI error:", error, info?.componentStack);
  }

  render() {
    if (!this.state.error) return this.props.children;

    return (
      <div className="error-panel" role="alert">
        <h2 className="error-panel-title">Something went wrong</h2>
        <p className="error-panel-body">
          This page hit an unexpected error. Reloading usually clears it.
          If it keeps happening, tell an administrator what you were doing
          at the time.
        </p>
        <p className="muted">{this.state.error?.message}</p>
        <button
          className="btn btn-gold"
          onClick={() => window.location.reload()}
        >
          Reload the page
        </button>
      </div>
    );
  }
}
