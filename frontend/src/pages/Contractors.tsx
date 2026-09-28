import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createContractor, listContractors } from "../api/contractors";
import { useAuth } from "../hooks/useAuth";

export default function Contractors() {
  const { hasRole } = useAuth();
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState("");
  const [regNo, setRegNo] = useState("");
  const [phone, setPhone] = useState("");

  const { data: contractors, isLoading } = useQuery({ queryKey: ["contractors"], queryFn: listContractors });
  const createMutation = useMutation({
    mutationFn: () => createContractor({ name, registration_number: regNo || undefined, phone: phone || undefined }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["contractors"] });
      setShowCreate(false);
      setName(""); setRegNo(""); setPhone("");
    },
  });

  const canCreate = hasRole("STATE_ADMIN", "DEPARTMENT_ADMIN");

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Contractors</h1>
          <p className="text-sm text-slate-500">Registered contractors available for project and work order assignment.</p>
        </div>
        {canCreate && <button onClick={() => setShowCreate((s) => !s)} className="bg-rb-navy text-white text-sm font-medium px-4 py-2 rounded-md">+ Add Contractor</button>}
      </div>

      {showCreate && (
        <div className="bg-white rounded-lg border border-slate-200 p-4 grid grid-cols-3 gap-3">
          <input placeholder="Name" value={name} onChange={(e) => setName(e.target.value)} className="rounded-md border border-slate-300 px-2 py-1.5 text-sm" />
          <input placeholder="Registration number" value={regNo} onChange={(e) => setRegNo(e.target.value)} className="rounded-md border border-slate-300 px-2 py-1.5 text-sm" />
          <input placeholder="Phone" value={phone} onChange={(e) => setPhone(e.target.value)} className="rounded-md border border-slate-300 px-2 py-1.5 text-sm" />
          <button disabled={!name || createMutation.isPending} onClick={() => createMutation.mutate()} className="bg-rb-teal text-white text-sm px-3 py-1.5 rounded-md disabled:opacity-50 col-span-3 w-fit">
            Add
          </button>
        </div>
      )}

      <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-50 text-slate-500 text-xs uppercase">
            <tr>
              <th className="text-left px-4 py-2">Name</th>
              <th className="text-left px-4 py-2">Registration No.</th>
              <th className="text-left px-4 py-2">Contact</th>
              <th className="text-left px-4 py-2">Phone</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {isLoading && <tr><td colSpan={4} className="px-4 py-6 text-center text-slate-400">Loading…</td></tr>}
            {contractors?.map((c) => (
              <tr key={c.id}>
                <td className="px-4 py-2 font-medium">{c.name}</td>
                <td className="px-4 py-2 font-mono text-xs">{c.registration_number ?? "—"}</td>
                <td className="px-4 py-2">{c.contact_person ?? "—"}</td>
                <td className="px-4 py-2">{c.phone ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
