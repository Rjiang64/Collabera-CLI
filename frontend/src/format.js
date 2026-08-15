// Small shared formatters so every page renders money the same way.

// money(5240) -> "$5,240.00"   |   money(8200, 0) -> "$8,200"
export function money(value, decimals = 2) {
  return `$${Number(value || 0).toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })}`;
}

// "Good morning" / "Good afternoon" / "Good evening" based on the local clock.
export function greeting(date = new Date()) {
  const h = date.getHours();
  if (h < 12) return "Good morning";
  if (h < 18) return "Good afternoon";
  return "Good evening";
}

// First name only, so the greeting reads "Good evening, Santosh" rather than
// echoing a full name or an email address.
export function firstName(user) {
  if (user?.full_name) return user.full_name.trim().split(/\s+/)[0];
  if (user?.email) return user.email.split("@")[0];
  return "there";
}
