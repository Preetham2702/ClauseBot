const API_BASE = import.meta.env.VITE_API_BASE;

export async function analyzeLease(file) {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) throw new Error("Request failed");
  return res.json();
}
