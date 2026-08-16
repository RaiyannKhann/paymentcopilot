import { VoxelTopographyGrid } from "@/components/ui/voxel-topography-grid";

/** Per-page animated background: sits above the shared AmbientBackdrop (-z-10) and below
    page content. Scrimmed so text/panels stay legible over the moving canvas. Not put in
    AmbientBackdrop itself — that's mounted on every route, and this is a per-frame canvas
    redraw that's only worth running on the app's few primary pages. */
export function VoxelBackdrop() {
  return (
    <div aria-hidden="true" className="pointer-events-none fixed inset-0 -z-[5] overflow-hidden">
      <VoxelTopographyGrid
        fill
        tileSize={40}
        maxHeight={45}
        primaryColor="#8b5cf6"
        wireColor="rgba(167, 139, 250, 0.3)"
        speed={0.008}
        backgroundColor="#07060f"
      />
      <div className="absolute inset-0 bg-gradient-to-b from-canvas/55 via-canvas/70 to-canvas" />
    </div>
  );
}
