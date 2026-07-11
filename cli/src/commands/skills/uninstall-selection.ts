/** Sentinel value for “select all” in interactive uninstall multiselect. */
export const UNINSTALL_ALL = '__all__';

/**
 * Resolve multiselect values to symlink paths to remove.
 * If the “all” sentinel is present, every installed path is returned
 * (individual checks are ignored — all means all).
 */
export function resolveUninstallSelection(
  selectedValues: string[],
  allSymlinkPaths: string[],
): string[] {
  if (selectedValues.includes(UNINSTALL_ALL)) {
    return [...allSymlinkPaths];
  }
  return selectedValues.filter((v) => v !== UNINSTALL_ALL);
}

export function buildUninstallMultiselectOptions(
  skills: Array<{ symlinkPath: string; bucket: string; name: string; target: string }>,
): Array<{ value: string; label: string; hint: string }> {
  return [
    {
      value: UNINSTALL_ALL,
      label: 'Todas as skills',
      hint: `remover as ${skills.length} instalada(s) neste projeto`,
    },
    ...skills.map((s) => ({
      value: s.symlinkPath,
      label: s.bucket ? `${s.bucket}/${s.name}` : s.name,
      hint: `${s.target} — ${s.symlinkPath}`,
    })),
  ];
}
