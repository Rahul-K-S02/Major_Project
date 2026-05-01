"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, RadarChart, Radar, PolarGrid, PolarAngleAxis } from "recharts";
import { Download, ArrowLeft, Dna, AlertCircle, CheckCircle, Info, ChevronDown, ChevronUp } from "lucide-react";

const DISEASE_META = {
  type2_diabetes:          { label: "Type 2 Diabetes",        icon: "🩸", color: "#E24B4A" },
  coronary_artery_disease: { label: "Coronary Artery Disease", icon: "❤️", color: "#E8593C" },
  breast_cancer:           { label: "Breast Cancer",           icon: "🎗️", color: "#D4537E" },
  alzheimers:              { label: "Alzheimer's Disease",     icon: "🧠", color: "#7F77DD" },
  hypertension:            { label: "Hypertension",            icon: "💊", color: "#378ADD" },
};

const RISK_STYLES = {
  Low:       { bg: "bg-green-50",  border: "border-green-200", text: "text-green-700",  badge: "bg-green-100 text-green-800" },
  Average:   { bg: "bg-blue-50",   border: "border-blue-200",  text: "text-blue-700",   badge: "bg-blue-100 text-blue-800" },
  Moderate:  { bg: "bg-yellow-50", border: "border-yellow-200",text: "text-yellow-700", badge: "bg-yellow-100 text-yellow-800" },
  High:      { bg: "bg-red-50",    border: "border-red-200",   text: "text-red-700",    badge: "bg-red-100 text-red-800" },
  "Very High":{ bg: "bg-red-100",  border: "border-red-300",   text: "text-red-800",    badge: "bg-red-200 text-red-900" },
};

export default function ResultsPage() {
  const router = useRouter();
  const [results, setResults]   = useState(null);
  const [profile, setProfile]   = useState(null);
  const [expanded, setExpanded] = useState({});
  const [activeTab, setActiveTab] = useState("overview");

  useEffect(() => {
    const r = sessionStorage.getItem("generisk_results");
    const p = sessionStorage.getItem("generisk_profile");
    if (!r) { router.push("/"); return; }
    setResults(JSON.parse(r));
    if (p) setProfile(JSON.parse(p));
  }, [router]);

  if (!results) return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <div className="w-12 h-12 border-4 border-accent border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p className="text-gray-500">Loading results...</p>
      </div>
    </div>
  );

  const { prs_results, fused_results, shap_charts, explanations, report_id, processing_time_sec } = results;

  // Chart data for overview bar chart
  const barData = Object.entries(prs_results || {}).map(([disease, data]) => ({
    name: DISEASE_META[disease]?.label || disease,
    multiplier: data.risk_multiplier || 1,
    level: data.risk_level,
    color: DISEASE_META[disease]?.color || "#888",
  }));

  // Radar chart data
  const radarData = Object.entries(prs_results || {}).map(([disease, data]) => ({
    subject: DISEASE_META[disease]?.label?.split(" ")[0] || disease,
    value: Math.min(data.risk_percent || 50, 100),
  }));

  function downloadPDF() {
    if (!results.pdf_base64) { alert("PDF not available — make sure ReportLab is installed on the server."); return; }
    const link = document.createElement("a");
    link.href = `data:application/pdf;base64,${results.pdf_base64}`;
    link.download = `GeneRisk_Report_${report_id}.pdf`;
    link.click();
  }

  function toggleExpand(disease) {
    setExpanded(e => ({ ...e, [disease]: !e[disease] }));
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navbar */}
      <nav className="bg-white border-b border-gray-100 px-6 py-4 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-4">
          <button onClick={() => router.push("/")} className="flex items-center gap-2 text-gray-500 hover:text-primary text-sm">
            <ArrowLeft className="w-4 h-4" /> New Analysis
          </button>
          <div className="flex items-center gap-2">
            <Dna className="w-5 h-5 text-primary" />
            <span className="font-bold text-primary">GeneRisk</span>
            <span className="text-gray-300">|</span>
            <span className="text-sm text-gray-500">Report #{report_id}</span>
          </div>
        </div>
        <button onClick={downloadPDF}
          className="flex items-center gap-2 bg-primary text-white px-4 py-2 rounded-xl text-sm font-medium hover:bg-accent transition-colors">
          <Download className="w-4 h-4" /> Download PDF
        </button>
      </nav>

      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-6 flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-primary">Your Genomic Risk Report</h1>
            <p className="text-gray-500 mt-1">
              Analysed in {processing_time_sec?.toFixed(1)}s · {profile?.age} years · {profile?.sex} · {profile?.ancestry?.replace("_", " ")}
            </p>
          </div>
          <div className="flex items-center gap-2 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-xl px-3 py-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            Research tool — not a medical diagnosis
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 bg-gray-100 rounded-xl p-1 mb-6 w-fit">
          {["overview","diseases","shap","fusion"].map(tab => (
            <button key={tab} onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all
                ${activeTab === tab ? "bg-white text-primary shadow-sm" : "text-gray-500 hover:text-gray-700"}`}>
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {/* ── TAB: OVERVIEW ── */}
        {activeTab === "overview" && (
          <div className="grid grid-cols-3 gap-6">
            {/* Risk bar chart */}
            <div className="col-span-2 bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
              <h2 className="font-bold text-primary mb-4">Risk Multiplier vs Population Average</h2>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={barData} layout="vertical" margin={{ left: 20 }}>
                  <XAxis type="number" domain={[0, 3]} tickFormatter={v => `${v}x`} fontSize={11} />
                  <YAxis type="category" dataKey="name" width={160} fontSize={11} />
                  <Tooltip formatter={(v) => [`${v.toFixed(2)}x population average`, "Risk"]} />
                  <Bar dataKey="multiplier" radius={4}>
                    {barData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
              <p className="text-xs text-gray-400 mt-2">1.0x = population average risk. Values above 1.0 indicate elevated genetic risk.</p>
            </div>

            {/* Radar + stats */}
            <div className="flex flex-col gap-4">
              <div className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm">
                <h2 className="font-bold text-primary mb-3 text-sm">Risk Profile Radar</h2>
                <ResponsiveContainer width="100%" height={180}>
                  <RadarChart data={radarData}>
                    <PolarGrid stroke="#E5E7EB" />
                    <PolarAngleAxis dataKey="subject" fontSize={10} />
                    <Radar name="Risk" dataKey="value" stroke="#2E75B6" fill="#2E75B6" fillOpacity={0.2} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
              <div className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm">
                <h2 className="font-bold text-primary mb-3 text-sm">Quick Summary</h2>
                {Object.entries(prs_results || {}).map(([disease, data]) => {
                  const meta = DISEASE_META[disease] || {};
                  const s = RISK_STYLES[data.risk_level] || RISK_STYLES.Average;
                  return (
                    <div key={disease} className="flex items-center justify-between py-1.5 border-b border-gray-50 last:border-0">
                      <span className="text-xs text-gray-600">{meta.icon} {meta.label?.split(" ")[0]}</span>
                      <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${s.badge}`}>{data.risk_level}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* ── TAB: DISEASES ── */}
        {activeTab === "diseases" && (
          <div className="space-y-4">
            {Object.entries(prs_results || {}).map(([disease, data]) => {
              const meta    = DISEASE_META[disease] || { label: disease, icon: "🧬", color: "#888" };
              const s       = RISK_STYLES[data.risk_level] || RISK_STYLES.Average;
              const fused   = fused_results?.[disease] || {};
              const explain = explanations?.[disease]?.explanation || "";
              const isOpen  = expanded[disease];

              return (
                <div key={disease} className={`bg-white rounded-2xl border ${s.border} shadow-sm overflow-hidden`}>
                  <div className="p-5 flex items-start justify-between cursor-pointer"
                    onClick={() => toggleExpand(disease)}>
                    <div className="flex items-center gap-4">
                      <div className="text-3xl">{meta.icon}</div>
                      <div>
                        <h3 className="font-bold text-primary">{meta.label}</h3>
                        <div className="flex items-center gap-3 mt-1">
                          <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${s.badge}`}>{data.risk_level}</span>
                          <span className="text-sm text-gray-500">{data.risk_multiplier}x population average</span>
                          <span className="text-xs text-gray-400">{data.snps_found} of {data.snps_total} key SNPs found</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="w-24">
                        <div className="w-full bg-gray-100 rounded-full h-2">
                          <div className="h-2 rounded-full transition-all" style={{ width: `${data.risk_percent}%`, backgroundColor: meta.color }} />
                        </div>
                        <p className="text-xs text-gray-400 mt-1 text-right">{data.risk_percent}%</p>
                      </div>
                      {isOpen ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
                    </div>
                  </div>

                  {isOpen && (
                    <div className={`px-5 pb-5 border-t ${s.border} pt-4`}>
                      {/* AI Explanation */}
                      {explain && (
                        <div className="bg-gray-50 rounded-xl p-4 mb-4">
                          <div className="flex items-center gap-2 mb-2">
                            <Info className="w-4 h-4 text-accent" />
                            <span className="text-sm font-semibold text-primary">AI Explanation</span>
                          </div>
                          <p className="text-sm text-gray-600 leading-relaxed">{explain}</p>
                        </div>
                      )}

                      {/* Contributing SNPs */}
                      {data.contributing_snps?.length > 0 && (
                        <div>
                          <p className="text-sm font-semibold text-primary mb-2">Contributing Genetic Variants</p>
                          <div className="overflow-x-auto">
                            <table className="w-full text-xs">
                              <thead>
                                <tr className="bg-gray-50 text-gray-500">
                                  <th className="text-left py-2 px-3 rounded-l-lg">Gene</th>
                                  <th className="text-left py-2 px-3">SNP ID</th>
                                  <th className="text-center py-2 px-3">Copies</th>
                                  <th className="text-right py-2 px-3 rounded-r-lg">Contribution</th>
                                </tr>
                              </thead>
                              <tbody>
                                {data.contributing_snps.slice(0, 5).map((snp, i) => (
                                  <tr key={i} className="border-b border-gray-50">
                                    <td className="py-2 px-3 font-semibold text-primary">{snp.gene}</td>
                                    <td className="py-2 px-3 font-mono text-blue-600">{snp.rs_id}</td>
                                    <td className="py-2 px-3 text-center">{snp.dosage}</td>
                                    <td className={`py-2 px-3 text-right font-semibold ${snp.contribution > 0 ? "text-red-600" : "text-green-600"}`}>
                                      {snp.contribution > 0 ? "+" : ""}{snp.contribution.toFixed(3)}
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      )}

                      {/* Fused risk */}
                      {fused.fused_risk_level && (
                        <div className="mt-4 flex items-center gap-3 text-sm bg-purple-50 rounded-xl p-3 border border-purple-100">
                          <CheckCircle className="w-4 h-4 text-purple-600 flex-shrink-0" />
                          <span className="text-gray-600">
                            <strong className="text-primary">Multimodal risk (genetics + lifestyle):</strong>{" "}
                            {fused.fused_risk_level} — Genetic {Math.round(fused.genetic_score * 100)}% · Lifestyle {Math.round(fused.lifestyle_score * 100)}%
                          </span>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* ── TAB: SHAP CHARTS ── */}
        {activeTab === "shap" && (
          <div className="grid grid-cols-2 gap-6">
            {Object.entries(shap_charts || {}).map(([disease, imgData]) => {
              const meta = DISEASE_META[disease] || { label: disease, icon: "🧬" };
              return (
                <div key={disease} className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm">
                  <h3 className="font-bold text-primary mb-1">{meta.icon} {meta.label}</h3>
                  <p className="text-xs text-gray-400 mb-3">Gene contributions — red = increases risk, green = decreases risk</p>
                  {imgData ? (
                    <img src={imgData} alt={`SHAP chart for ${meta.label}`} className="w-full rounded-lg" />
                  ) : (
                    <div className="h-32 flex items-center justify-center text-gray-300 text-sm bg-gray-50 rounded-lg">
                      No variants found for this disease
                    </div>
                  )}
                </div>
              );
            })}
            <div className="col-span-2 bg-blue-50 rounded-2xl p-4 border border-blue-100 text-sm text-blue-700">
              <strong>About SHAP:</strong> Each bar shows how much a specific gene variant contributed to your risk score.
              Positive values (red) increase your risk; negative values (green) decrease it.
              The longer the bar, the stronger the effect of that gene.
            </div>
          </div>
        )}

        {/* ── TAB: FUSION ── */}
        {activeTab === "fusion" && (
          <div className="space-y-4">
            <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm mb-4">
              <h2 className="font-bold text-primary mb-2">Multimodal Risk Fusion</h2>
              <p className="text-sm text-gray-500">Your overall risk combines 60% genetic factors and 40% lifestyle factors. This gives a more complete picture than genetics alone.</p>
            </div>
            {Object.entries(fused_results || {}).map(([disease, data]) => {
              const meta = DISEASE_META[disease] || { label: disease, icon: "🧬" };
              const gPct = Math.round((data.genetic_score || 0) * 100);
              const lPct = Math.round((data.lifestyle_score || 0) * 100);
              return (
                <div key={disease} className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-semibold text-primary">{meta.icon} {meta.label}</h3>
                    <span className={`text-sm font-bold px-3 py-1 rounded-full
                      ${(RISK_STYLES[data.fused_risk_level] || RISK_STYLES.Average).badge}`}>
                      {data.fused_risk_level}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-xs text-gray-500 mb-1">Genetic contribution (60%)</p>
                      <div className="w-full bg-gray-100 rounded-full h-3">
                        <div className="h-3 rounded-full bg-blue-500" style={{ width: `${gPct}%` }} />
                      </div>
                      <p className="text-xs text-blue-600 font-semibold mt-1">{gPct}%</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500 mb-1">Lifestyle contribution (40%)</p>
                      <div className="w-full bg-gray-100 rounded-full h-3">
                        <div className="h-3 rounded-full bg-orange-400" style={{ width: `${lPct}%` }} />
                      </div>
                      <p className="text-xs text-orange-600 font-semibold mt-1">{lPct}%</p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Disclaimer */}
        <div className="mt-8 bg-gray-100 rounded-2xl p-5 text-xs text-gray-500 leading-relaxed">
          <strong className="text-gray-700">⚠ Medical Disclaimer:</strong> This report is generated by an AI system for educational and research purposes only.
          It is NOT a medical diagnosis. Risk scores are probabilistic indicators based on population genetics studies.
          Please consult a qualified physician or genetic counsellor before making any health decisions.
          Developed by JNNCE Batch B13 — GeneRisk Final Year Project, VTU.
        </div>
      </div>
    </div>
  );
}
