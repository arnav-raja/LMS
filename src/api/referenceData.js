import { adminApi } from "./endpoints";

/*
 * Departments and seniorities live in one place — app/constants.py on the
 * backend. Everything here fetches that list once per session and caches it,
 * instead of keeping a second hardcoded copy in sync by hand.
 */

let cache = null; // { departments: [{code, label}], seniorities: [string] }
let pending = null;

export function loadReferenceData() {
  if (cache) return Promise.resolve(cache);
  if (pending) return pending;

  pending = Promise.all([adminApi.departments(), adminApi.roles()])
    .then(([departments, roles]) => {
      cache = {
        departments,
        seniorities: roles.map((role) => role.value),
      };
      return cache;
    })
    .finally(() => {
      pending = null;
    });

  return pending;
}

export function clearReferenceData() {
  cache = null;
  pending = null;
}

export function getReferenceData() {
  return cache;
}

export function departmentLabel(code) {
  return cache?.departments.find((d) => d.code === code)?.label || code || "Unassigned";
}
