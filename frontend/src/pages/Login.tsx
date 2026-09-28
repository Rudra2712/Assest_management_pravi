import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Landmark } from "lucide-react";
import { useAuth } from "../hooks/useAuth";

const DEMO_USERS = [
  { label: "State Admin", email: "state.admin@rnb.gov.in" },
  { label: "Department Admin", email: "dept.admin@rnb.gov.in" },
  { label: "Field Engineer", email: "field.engineer@rnb.gov.in" },
  { label: "Maintenance Officer", email: "maintenance.officer@rnb.gov.in" },
  { label: "Contractor", email: "contractor.user@rnb.gov.in" },
];

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("state.admin@rnb.gov.in");
  const [password, setPassword] = useState("Password123!");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function submitLogin(loginEmail: string) {
    setError(null);
    setSubmitting(true);
    try {
      const authenticatedUser = await login(loginEmail, password);
      navigate(authenticatedUser.roles.includes("CONTRACTOR") ? "/tenders" : "/dashboard");
    } catch {
      setError("Incorrect email or password.");
    } finally {
      setSubmitting(false);
    }
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    await submitLogin(email);
  }

  return (
    <div
      className="min-h-screen flex items-center justify-center px-4 py-8"
      style={{ background: "radial-gradient(ellipse at 0% 0%, #e8faf3 0%, #f8fffe 40%, #ffffff 100%)" }}
    >
      <div className="w-full max-w-md bg-white rounded-2xl shadow-[0_32px_80px_rgba(0,0,0,0.08),0_2px_8px_rgba(0,0,0,0.04)] p-8 animate-fadeUp">
        <div className="text-center mb-6">
          <div className="w-10 h-10 rounded-[11px] bg-brand flex items-center justify-center mx-auto mb-3 animate-pulseBrand">
            <Landmark size={20} className="text-brand-ink" />
          </div>
          <div className="text-xs uppercase tracking-wide text-slate-400 font-semibold">Government of Gujarat</div>
          <h1 className="text-xl font-extrabold text-ink mt-1 tracking-tight">R&amp;B Asset Inventory</h1>
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
              className="w-full rounded-[10px] border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm outline-none transition-all focus:bg-white focus:border-brand focus:ring-4 focus:ring-brand/15"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-[10px] border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm outline-none transition-all focus:bg-white focus:border-brand focus:ring-4 focus:ring-brand/15"
            />
          </div>
          {error && <div className="text-sm text-red-600">{error}</div>}
          <button
            type="submit"
            disabled={submitting}
            className="w-full bg-brand text-brand-ink rounded-[10px] py-2.5 text-sm font-bold tracking-wide hover:bg-brand-dark hover:-translate-y-0.5 hover:shadow-[0_6px_20px_rgba(110,207,163,0.4)] transition-all disabled:opacity-60 disabled:translate-y-0 disabled:shadow-none"
          >
            {submitting ? "Signing in…" : "Sign in"}
          </button>
        </form>
        <div className="mt-6 border-t border-slate-100 pt-4">
          <h2 className="text-sm font-semibold text-slate-700 mb-3">Quick demo login</h2>
          <div className="grid grid-cols-2 gap-2">
            {DEMO_USERS.map((demoUser) => (
              <button
                key={demoUser.email}
                type="button"
                disabled={submitting}
                onClick={() => {
                  setEmail(demoUser.email);
                  void submitLogin(demoUser.email);
                }}
                className="min-h-10 rounded-[10px] border border-slate-200 px-3 py-2 text-left text-xs font-medium text-slate-600 hover:border-brand hover:bg-brand-light hover:text-ink transition-colors disabled:opacity-50"
              >
                {demoUser.label}
              </button>
            ))}
          </div>
          <p className="mt-3 text-xs text-slate-400">Demo password: Password123!</p>
        </div>
      </div>
    </div>
  );
}
