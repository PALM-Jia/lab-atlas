(function (root) {
  "use strict";
  root.atlasMixedNodeSizes = (absoluteSizes, { min = 8, max = 50 } = {}) => {
    if (!absoluteSizes.length) return [];
    const low = Math.min(...absoluteSizes),
      high = Math.max(...absoluteSizes);
    // Equal values retain their absolute size; filtering cannot create a distinction.
    if (high === low) return absoluteSizes.slice();
    return absoluteSizes.map(
      (size) =>
        0.5 * size + 0.5 * (min + ((size - low) / (high - low)) * (max - min)),
    );
  };
  if (typeof module !== "undefined" && module.exports)
    module.exports = root.atlasMixedNodeSizes;
})(typeof window !== "undefined" ? window : globalThis);
