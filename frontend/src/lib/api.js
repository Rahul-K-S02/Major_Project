import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({ baseURL: API_URL, timeout: 120000 });

export async function analyzeGenome(payload) {
  const { data } = await api.post("/analyze", payload);
  return data;
}

export async function healthCheck() {
  const { data } = await api.get("/health");
  return data;
}

export const DISEASES = {
  type2_diabetes:           { label: "Type 2 Diabetes",         icon: "🩸" },
  coronary_artery_disease:  { label: "Coronary Artery Disease",  icon: "❤️" },
  breast_cancer:            { label: "Breast Cancer",            icon: "🎗️" },
  alzheimers:               { label: "Alzheimer's Disease",      icon: "🧠" },
  hypertension:             { label: "Hypertension",             icon: "💊" },
};

export function riskColor(level) {
  const map = { Low: "text-green-600", Average: "text-blue-600",
    Moderate: "text-yellow-600", High: "text-red-600", "Very High": "text-red-800" };
  return map[level] || "text-gray-600";
}

export function riskBg(level) {
  const map = { Low: "bg-green-50 border-green-200", Average: "bg-blue-50 border-blue-200",
    Moderate: "bg-yellow-50 border-yellow-200", High: "bg-red-50 border-red-200",
    "Very High": "bg-red-100 border-red-300" };
  return map[level] || "bg-gray-50 border-gray-200";
}
