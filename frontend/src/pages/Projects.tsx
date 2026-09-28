import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createProject, listProjects } from "../api/projects";
import { listAdminUnits, listDepartments } from "../api/admin";
import { listContractors } from "../api/contractors";
import { useAuth } from "../hooks/useAuth";

const STATUS_COLORS: Record<string, string> = {
  PROPOSED: "bg-slate-100 text-slate-600",
  SANCTIONED: "bg-sky-100 text-sky-700",
  IN_PROGRESS: "bg-amber-100 text-amber-800",
  COMPLETED: "bg-emerald-100 text-emerald-700",
  CLOSED: "bg-slate-200 text-slate-700",
};

export default function Projects() {
  const { hasRole } = useAuth();
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [projectCode, setProjectCode] = useState("");
  const [name, setName] = useState("");
  const [departmentId, setDepartmentId] = useState("");
  const [administrativeUnitId, setAdministrativeUnitId] = useState("");
  const [contractorId, setContractorId] = useState("");
  const [budget, setBudget] = useState("");

  const { data: projects, isLoading } = useQuery({ queryKey: ["projects"], queryFn: listProjects });
  const { data: departments } = useQuery({ queryKey: ["departments"], queryFn: listDepartments });
  const { data: adminUnits } = useQuery({ queryKey: ["admin-units"], queryFn: listAdminUnits });
  const { data: contractors } = useQuery({ queryKey: ["contractors"], queryFn: listContractors });

  const createMutation = useMutation({
    mutationFn: () =>
      createProject({
        project_code: projectCode,
        name,
        department_id: departmentId,
        administrative_unit_id: administrativeUnitId,
        contractor_id: contractorId || undefined,
        sanctioned_budget: budget ? Number(budget) : undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      setShowCreate(false);
      setProjectCode(""); setName(""); setBudget("");
    },
  });

  const canCreate = hasRole("STATE_ADMIN", "DEPARTMENT_ADMIN", "CIRCLE_DIVISION_OFFICER");

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Projects</h1>
          <p className="text-sm text-slate-500">Sanction, budget, contractor and construction tracking through to asset commissioning.</p>
        </div>
        {canCreate && <button onClick={() => setShowCreate((s) => !s)} className="bg-rb-navy text-white text-sm font-medium px-4 py-2 rounded-md">+ New Project</button>}
      </div>

      {showCreate && (
        <div className="bg-white rounded-lg border border-slate-200 p-4 grid grid-cols-3 gap-3">
          <input placeholder="Project code" value={projectCode} onChange={(e) => setProjectCode(e.target.value)} className="rounded-md border border-slate-300 px-2 py-1.5 text-sm" />
          <input placeholder="Name" value={name} onChange={(e) => setName(e.target.value)} className="rounded-md border border-slate-300 px-2 py-1.5 text-sm col-span-2" />
          <select value={departmentId} onChange={(e) => setDepartmentId(e.target.value)} className="rounded-md border border-slate-300 px-2 py-1.5 text-sm">
            <option value="">Department…</option>
            {departments?.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
          </select>
          <select value={administrativeUnitId} onChange={(e) => setAdministrativeUnitId(e.target.value)} className="rounded-md border border-slate-300 px-2 py-1.5 text-sm">
            <option value="">Administrative unit…</option>
            {adminUnits?.map((u) => <option key={u.id} value={u.id}>{u.name}</option>)}
          </select>
          <select value={contractorId} onChange={(e) => setContractorId(e.target.value)} className="rounded-md border border-slate-300 px-2 py-1.5 text-sm">
            <option value="">Contractor (optional)…</option>
            {contractors?.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
          <input placeholder="Sanctioned budget" type="number" value={budget} onChange={(e) => setBudget(e.target.value)} className="rounded-md border border-slate-300 px-2 py-1.5 text-sm" />
          <button
            disabled={!projectCode || !name || !departmentId || !administrativeUnitId || createMutation.isPending}
            onClick={() => createMutation.mutate()}
            className="bg-rb-teal text-white text-sm px-3 py-1.5 rounded-md disabled:opacity-50 col-span-3 w-fit"
          >
            Create Project
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {isLoading && <div className="text-slate-400">Loading…</div>}
        {projects?.map((p) => (
          <div key={p.id} className="bg-white rounded-lg border border-slate-200 p-4">
            <div className="flex justify-between items-start">
              <div>
                <div className="text-xs font-mono text-slate-500">{p.project_code}</div>
                <div className="font-medium text-slate-900">{p.name}</div>
              </div>
              <span className={`text-xs px-2 py-0.5 rounded ${STATUS_COLORS[p.status]}`}>{p.status.replaceAll("_", " ")}</span>
            </div>
            <p className="text-sm text-slate-500 mt-1">{p.description}</p>
            <div className="text-xs text-slate-500 mt-2 space-y-0.5">
              <div>Sanctioned: {p.sanctioned_budget ? `₹${p.sanctioned_budget.toLocaleString()}` : "—"}</div>
              <div>Expenditure: {p.actual_expenditure ? `₹${p.actual_expenditure.toLocaleString()}` : "—"}</div>
              <div>Expected completion: {p.expected_completion_date ?? "—"}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
