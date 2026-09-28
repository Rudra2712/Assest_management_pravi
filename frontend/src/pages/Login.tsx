import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("state.admin@rnb.gov.in");
  const [password, setPassword] = useState("Password123!");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password);
      navigate("/dashboard");
    } catch {
      setError("Incorrect email or password.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-rb-navy px-4">
      <div className="w-full max-w-sm bg-white rounded-lg shadow-lg p-8">
        <div className="text-center mb-6">
          <div className="text-xs uppercase tracking-wide text-slate-500">Government of Pravinagar</div>
          <h1 className="text-xl font-semibold text-rb-navy mt-1">R&amp;B Asset Inventory</h1>
          <p className="text-sm text-slate-500 mt-1">Immovable Physical Asset Inventory &amp; Lifecycle Management</p>
        </div>
        <form onSubmit={onSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-rb-teal"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-rb-teal"
            />
          </div>
          {error && <div className="text-sm text-red-600">{error}</div>}
          <button
            type="submit"
            disabled={submitting}
            className="w-full bg-rb-navy text-white rounded-md py-2 text-sm font-medium hover:bg-rb-navy/90 disabled:opacity-50"
          >
            {submitting ? "Signing in…" : "Sign in"}
          </button>
        </form>
        <div className="mt-6 text-xs text-slate-400 border-t pt-4">
          Demo accounts (password: Password123!): state.admin, dept.admin, circle.north, subdivision.n1a, field.engineer,
          maintenance.officer, auditor, contractor.user — all @rnb.gov.in
        </div>
      </div>
    </div>
  );
}
