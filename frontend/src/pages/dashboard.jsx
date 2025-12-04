import { useState } from "react";
import LeftPanel from "../components/left_panel";
import MiddlePanel from "../components/middle_panel";
import RightChatPanel from "../components/right_panel";

export default function Dashboard() {
  const [file, setFile] = useState(null);

  const pdfUrl = file ? URL.createObjectURL(file) : null;

  return (
    <div className="w-full h-screen flex bg-[#0D0D0F] text-gray-200 p-3 gap-3 overflow-hidden">

      {/* LEFT PANEL */}
      <div
        className="
          w-[22%]
          overflow-hidden 
          bg-[#1A1A1D] 
          border border-[rgba(255,80,80,0.35)]
          rounded-2xl 
          shadow-[0_0_18px_rgba(255,80,80,0.25)]
      ">
        <LeftPanel 
          onFileUpload={setFile}
          pdfUrl={pdfUrl}
        />
      </div>

      {/* MIDDLE PANEL */}
      <div
        className="
          w-[48%]
          overflow-hidden 
          bg-[#1A1A1D] 
          border border-[rgba(255,80,80,0.35)]
          rounded-2xl 
          shadow-[0_0_18px_rgba(255,80,80,0.25)]
      ">
        <MiddlePanel file={file} />
      </div>

      {/* RIGHT PANEL */}
      <div
        className="
          w-[30%]
          overflow-hidden 
          flex flex-col 
          bg-[#1A1A1D]
          border border-[rgba(255,80,80,0.35)]
          rounded-2xl 
          shadow-[0_0_18px_rgba(255,80,80,0.25)]
      ">
        <RightChatPanel />
      </div>

    </div>
  );
}
