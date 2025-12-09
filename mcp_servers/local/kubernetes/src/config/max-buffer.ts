export function getSpawnMaxBuffer(): number {
  return parseInt(process.env.SPAWN_MAX_BUFFER || "1048577", 10);
}
