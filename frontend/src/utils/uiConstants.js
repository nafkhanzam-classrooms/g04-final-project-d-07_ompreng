export const ROLE_LABELS = { student: "Student", teacher: "Teacher", admin: "Admin" };

export function roleLabel(role) {
  if (!role) return "Online";
  return ROLE_LABELS[role] || role;
}