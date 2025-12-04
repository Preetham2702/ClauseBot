import { useEffect, useState } from "react";

export default function MiddlePanel({ file }) {
  const [fileUrl, setFileUrl] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Turn file into blob URL for PDF rendering (optional)
  useEffect(() => {
    if (!file) {
      setFileUrl(null);
      setAnalysis(null);
      setError("");
      return;
    }

    const url = URL.createObjectURL(file);
    setFileUrl(url);

    return () => URL.revokeObjectURL(url);
  }, [file]);


  // Upload file to backend and get analysis
  useEffect(() => {
    if (!file) return;

    const uploadAndAnalyze = async () => {
      setLoading(true);
      setError("");
      setAnalysis(null);

      try {
        const formData = new FormData();
        formData.append("file", file);

        const res = await fetch("http://localhost:8000/analyze-lease", {
          method: "POST",
          body: formData,
        });

        if (!res.ok) {
          const msg = await res.json();
          throw new Error(msg.detail || "Failed to analyze file");
        }

        const data = await res.json();
        setAnalysis(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    uploadAndAnalyze();

  }, [file]);


  return (
    <div className="w-full h-full flex flex-col bg-[#1A1A1A]">

      {/* HEADER */}
      <div className="
        w-full 
        text-center 
        py-4 
        border-b border-[rgba(255,80,80,0.3)]
        shadow-[0_3px_18px_rgba(255,80,80,0.25)]
      ">
        <h1 className="
          text-2xl 
          font-semibold 
          tracking-widest 
          text-white
          drop-shadow-[0_0_12px_rgba(255,80,80,0.5)]
          select-none
          uppercase
        ">
          Clause Bot
        </h1>
      </div>


      {/* BODY */}
      <div className="flex-1 w-full overflow-y-auto p-6 text-gray-200">

        {/* No file state */}
        {!file && (
          <p className="text-center text-gray-500 mt-20">
            No file to analyze
          </p>
        )}

        {/* Loading */}
        {loading && (
          <p className="text-center text-gray-400 mt-20 animate-pulse">
            Analyzing document...
          </p>
        )}

        {/* Error */}
        {error && (
          <p className="text-center text-red-400 mt-10">
            {error}
          </p>
        )}

        {/* Analysis Result */}
        {analysis && !loading && (
          <div className="space-y-6">

            {/* Summary */}
            <div>
              <h2 className="text-xl font-bold text-[#FF8A8A] mb-2">
                Summary
              </h2>
              <p className="text-gray-300 leading-relaxed">
                {analysis.summary}
              </p>
            </div>

            {/* Pros */}
            <div>
              <h2 className="text-xl font-bold text-[#8DFF8A] mb-2">
                Pros
              </h2>
              <ul className="list-disc ml-6 space-y-1">
                {analysis.pros.map((p, idx) => (
                  <li key={idx} className="text-gray-300">{p}</li>
                ))}
              </ul>
            </div>

            {/* Cons */}
            <div>
              <h2 className="text-xl font-bold text-[#FF8A8A] mb-2">
                Cons / Risks
              </h2>
              <ul className="list-disc ml-6 space-y-1">
                {analysis.cons.map((c, idx) => (
                  <li key={idx} className="text-gray-300">{c}</li>
                ))}
              </ul>
            </div>

            {/* Important Points */}
            <div>
              <h2 className="text-xl font-bold text-[#FFA76F] mb-2">
                Important Points
              </h2>
              <ul className="list-disc ml-6 space-y-1">
                {analysis.important_points.map((p, idx) => (
                  <li key={idx} className="text-gray-300">{p}</li>
                ))}
              </ul>
            </div>

          </div>
        )}

      </div>
    </div>
  );
}
