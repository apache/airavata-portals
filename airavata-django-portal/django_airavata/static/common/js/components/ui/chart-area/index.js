export { default as AreaChart } from "./AreaChart.vue";
// Re-export the curve-type enum so consumers can pick a curve without taking a
// direct dependency on @unovis (which is installed in this common package).
export { CurveType } from "@unovis/ts";
