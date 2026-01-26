export async function analyzeLease(file) {
    const formData = new FormData();
    formData.append("file", file);
  
    try {
      const res = await fetch("https://clausebot.preethamreddy2702.workers.dev", {
        method: "POST",
        body: formData
      });
  
      if (!res.ok) {
        const err = await res.json();
        console.error("Error:", err);
        return null;
      }
  
      const data = await res.json();
      return data;
  
    } catch (error) {
      console.error("Request failed:", error);
      return null;
    }
  }
  