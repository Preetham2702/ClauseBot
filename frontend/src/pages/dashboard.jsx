import { useEffect, useState } from "react";
import LeftPanel from "../components/left_panel";
import MiddlePanel from "../components/middle_panel";
import RightChatPanel from "../components/right_panel";

export default function Dashboard() {
  const [file, setFile] = useState(null);
  const [pdfUrl, setPdfUrl] = useState(null);

  // base64 -> File (used after refresh to rebuild file and re-run analysis)
  const base64ToFile = async (base64, filename = "contract.pdf") => {
    const res = await fetch(base64);
    const blob = await res.blob();
    return new File([blob], filename, { type: "application/pdf" });
  };

  // File -> base64 (store PDF so it survives refresh)
  const fileToBase64 = (f) =>
    new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result);
      reader.onerror = reject;
      reader.readAsDataURL(f);
    });

  // ✅ CLEAR DOCUMENT
  const clearDocument = () => {
    setFile(null);

    // cleanup blob if currently set
    if (pdfUrl?.startsWith("blob:")) {
      URL.revokeObjectURL(pdfUrl);
    }

    setPdfUrl(null);
    localStorage.removeItem("pdfBase64");
  };

  // On refresh: restore PDF + restore File (so analysis can rerun)
  useEffect(() => {
    const saved = localStorage.getItem("pdfBase64");
    if (!saved) return;

    setPdfUrl(saved);

    (async () => {
      const restoredFile = await base64ToFile(saved, "restored.pdf");
      setFile(restoredFile); // ✅ triggers middle auto-analysis again
    })();
  }, []);

  // Clean up blob urls when pdfUrl changes/unmounts
  useEffect(() => {
    return () => {
      if (pdfUrl?.startsWith("blob:")) URL.revokeObjectURL(pdfUrl);
    };
  }, [pdfUrl]);

  // Upload handler
  const handleFileUpload = async (newFile) => {
    setFile(newFile);

    // fast preview
    const blobUrl = URL.createObjectURL(newFile);
    setPdfUrl(blobUrl);

    // persist for refresh
    const b64 = await fileToBase64(newFile);
    localStorage.setItem("pdfBase64", b64);
  };

  return (
    <div className="w-full h-screen flex bg-[#0D0D0F] text-gray-200 p-3 gap-3 overflow-hidden">
      {/* LEFT */}
      <div className="w-[22%] overflow-hidden bg-[#1A1A1D] border border-[rgba(255,80,80,0.35)] rounded-2xl shadow-[0_0_18px_rgba(255,80,80,0.25)]">
        <LeftPanel
          onFileUpload={handleFileUpload}
          pdfUrl={pdfUrl}
          onClear={clearDocument}   // ✅ pass clear
        />
      </div>

      {/* MIDDLE */}
      <div className="w-[48%] overflow-hidden bg-[#1A1A1D] border border-[rgba(255,80,80,0.35)] rounded-2xl shadow-[0_0_18px_rgba(255,80,80,0.25)]">
        <MiddlePanel file={file} />
      </div>

      {/* RIGHT */}
      <div className="w-[30%] overflow-hidden flex flex-col bg-[#1A1A1D] border border-[rgba(255,80,80,0.35)] rounded-2xl shadow-[0_0_18px_rgba(255,80,80,0.25)]">
        <RightChatPanel />
      </div>
    </div>
  );
}
