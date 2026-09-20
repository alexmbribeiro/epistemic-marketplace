"use client";

import { useEffect, useRef } from "react";
import * as d3 from "d3";
import type { ArgumentGraph, ArgumentNode, ArgumentEdge } from "@/types";

const EDGE_COLORS: Record<string, string> = {
  supports: "#22d3ee",
  contradicts: "#f43f5e",
  qualifies: "#f59e0b",
  redefines: "#a78bfa",
  updates: "#64748b",
  uncertain: "#94a3b8",
};

interface Props {
  graph: ArgumentGraph;
}

export default function ArgumentGraphViz({ graph }: Props) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current || !graph.nodes.length) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const width = svgRef.current.clientWidth || 600;
    const height = 400;

    const simulation = d3
      .forceSimulation(graph.nodes as d3.SimulationNodeDatum[])
      .force("link", d3.forceLink(graph.edges).id((d: any) => d.id).distance(100))
      .force("charge", d3.forceManyBody().strength(-200))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide(40));

    const defs = svg.append("defs");
    Object.entries(EDGE_COLORS).forEach(([type, color]) => {
      defs
        .append("marker")
        .attr("id", `arrow-${type}`)
        .attr("viewBox", "0 -5 10 10")
        .attr("refX", 20)
        .attr("refY", 0)
        .attr("markerWidth", 6)
        .attr("markerHeight", 6)
        .attr("orient", "auto")
        .append("path")
        .attr("d", "M0,-5L10,0L0,5")
        .attr("fill", color);
    });

    const link = svg
      .append("g")
      .selectAll("line")
      .data(graph.edges)
      .join("line")
      .attr("stroke", (d) => EDGE_COLORS[d.type] || "#64748b")
      .attr("stroke-width", (d) => Math.max(1, d.strength * 3))
      .attr("stroke-opacity", 0.7)
      .attr("marker-end", (d) => `url(#arrow-${d.type})`);

    const node = (svg
      .append("g")
      .selectAll("g")
      .data(graph.nodes)
      .join("g") as d3.Selection<SVGGElement, any, SVGGElement, unknown>)
      .call(
        d3.drag<SVGGElement, any>()
          .on("start", (event, d) => { if (!event.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
          .on("drag", (event, d) => { d.fx = event.x; d.fy = event.y; })
          .on("end", (event, d) => { if (!event.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; })
      );

    node
      .append("circle")
      .attr("r", (d: any) => (d.type === "claim" ? 18 : 14))
      .attr("fill", (d: any) => {
        if (d.type === "claim") return "#6366f1";
        if (d.belief_score === undefined) return "#334155";
        return d.belief_score > 0.6 ? "#0e7490" : d.belief_score < 0.4 ? "#be123c" : "#92400e";
      })
      .attr("stroke", "#1e293b")
      .attr("stroke-width", 2);

    node
      .append("text")
      .text((d: any) => d.label.split(" ")[0])
      .attr("text-anchor", "middle")
      .attr("dy", "0.35em")
      .attr("font-size", 9)
      .attr("fill", "white")
      .attr("pointer-events", "none");

    simulation.on("tick", () => {
      link
        .attr("x1", (d: any) => d.source.x)
        .attr("y1", (d: any) => d.source.y)
        .attr("x2", (d: any) => d.target.x)
        .attr("y2", (d: any) => d.target.y);

      node.attr("transform", (d: any) => `translate(${d.x},${d.y})`);
    });

    return () => { simulation.stop(); };
  }, [graph]);

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-3 text-xs">
        {Object.entries(EDGE_COLORS).map(([type, color]) => (
          <div key={type} className="flex items-center gap-1">
            <div className="w-4 h-0.5 rounded" style={{ backgroundColor: color }} />
            <span className="text-slate-400">{type}</span>
          </div>
        ))}
      </div>
      <svg ref={svgRef} className="w-full rounded-lg bg-slate-900/50" height={400} />
    </div>
  );
}
