import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import AppLayout from "@/components/AppLayout";
import "@/index.css";
import AnalysisPage from "@/pages/AnalysisPage";
import PatientsPage from "@/pages/PatientsPage";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route index element={<Navigate to="/pacientes" replace />} />
          <Route path="/pacientes" element={<PatientsPage />} />
          <Route path="/analise" element={<AnalysisPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/pacientes" replace />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>,
);
