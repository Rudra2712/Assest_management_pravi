import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { assignUserRole, createUser, listAdminUnits, listDepartments, listUsers } from "../api/admin";

const ROLES = [
  "STATE_ADMIN", "DEPARTMENT_ADMIN", "CIRCLE_DIVISION_OFFICER", "SUB_DIVISION_OFFICER",
  "FIELD_ENGINEER", "MAINTENANCE_OFFICER", "CONTRACTOR", "AUDITOR",
];

export default function UserManagement() {
  const queryClient = useQueryClient();
  const { data: users, isLoading } = useQuery({ queryKey: ["users"], queryFn: listUsers });
  const { data: departments } = useQuery({ queryKey: ["departments"], queryFn: listDepartments });
  const { data: adminUnits } = useQuery({ queryKey: ["admin-units"], queryFn: listAdminUnits });

  const [showCreate, setShowCreate] = useState(false);
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [departmentId, setDepartmentId] = useState("");
  const [administrativeUnitId, setAdministrativeUnitId] = useState("");
  const [roleCode, setRoleCode] = useState(ROLES[3]);

  const createMutation = useMutation({
    mutationFn: () =>
      createUser({
        email, full_name: fullName, password,
        department_id: departmentId || undefined,
        administrative_unit_id: administrativeUnitId || undefined,
        role_codes: [roleCode],
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
      setShowCreate(false);
      setEmail(""); setFullName(""); setPassword("");
    },
  });

  const roleMutation = useMutation({
    mutationFn: ({ userId, role }: { userId: string; role: string }) => assignUserRole(userId, role),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["users"] }),
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">User Management</h1>
          <p className="text-sm text-slate-500">Accounts, roles and jurisdiction assignment.</p>
        </div>
        <button onClick={() => setShowCreate((s) => !s)} className="bg-rb-navy text-white text-sm font-medium px-4 py-2 rounded-md">+ Add User</button>
      </div>

      {showCreate && (
        <div className="bg-white rounded-lg border border-slate-200 p-4 grid grid-cols-3 gap-3">
          <input placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} className="rounded-md border border-slate-300 px-2 py-1.5 text-sm" />
          <input placeholder="Full name" value={fullName} onChange={(e) => setFullName(e.target.value)} className="rounded-md border border-slate-300 px-2 py-1.5 text-sm" />
          <input placeholder="Temporary password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="rounded-md border border-slate-300 px-2 py-1.5 text-sm" />
          <select value={departmentId} onChange={(e) => setDepartmentId(e.target.value)} className="rounded-md border border-slate-300 px-2 py-1.5 text-sm">
            <option value="">Department…</option>
            {departments?.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
          </select>
          <select value={administrativeUnitId} onChange={(e) => setAdministrativeUnitId(e.target.value)} className="rounded-md border border-slate-300 px-2 py-1.5 text-sm">
            <option value="">Administrative unit…</option>
            {adminUnits?.map((u) => <option key={u.id} value={u.id}>{u.name}</option>)}
          </select>
          <select value={roleCode} onChange={(e) => setRoleCode(e.target.value)} className="rounded-md border border-slate-300 px-2 py-1.5 text-sm">
            {ROLES.map((r) => <option key={r} value={r}>{r.replaceAll("_", " ")}</option>)}
          </select>
          <button disabled={!email || !fullName || !password || createMutation.isPending} onClick={() => createMutation.mutate()} className="bg-rb-teal text-white text-sm px-3 py-1.5 rounded-md disabled:opacity-50 col-span-3 w-fit">
            Create User
          </button>
        </div>
      )}

      <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
            <tr>
              <th className="text-left px-4 py-2">Name</th>
              <th className="text-left px-4 py-2">Email</th>
              <th className="text-left px-4 py-2">Roles</th>
              <th className="text-left px-4 py-2">Add Role</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {isLoading && <tr><td colSpan={4} className="px-4 py-6 text-center text-slate-400">Loading…</td></tr>}
            {users?.map((u) => (
              <tr key={u.id}>
                <td className="px-4 py-2">{u.full_name}</td>
                <td className="px-4 py-2 text-slate-500">{u.email}</td>
                <td className="px-4 py-2">{u.roles.join(", ") || "—"}</td>
                <td className="px-4 py-2">
                  <select
                    defaultValue=""
                    onChange={(e) => e.target.value && roleMutation.mutate({ userId: u.id, role: e.target.value })}
                    className="text-xs rounded border border-slate-300 px-1 py-0.5"
                  >
                    <option value="" disabled>Grant role…</option>
                    {ROLES.map((r) => <option key={r} value={r}>{r.replaceAll("_", " ")}</option>)}
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
