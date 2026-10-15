# Gathering 29 image process

Used built-in image generation once, referencing the full Gathering 28 wall
retrieved from its numbered record's exact artifact hash. Requested the same
1254 px square framing, unchanged ancestral rock/lighting/marks and Pepe, with
only a small worn charcoal triangular trail joining three red ochre pebble dabs
on bare rock beside the bridge. Requested no new hands, words, numbers, logos,
frames, people or political symbols. The trail represents an evidenced cycle.

The model placed its motif slightly left of the requested center. We kept that
placement on bare rock; did not move an ancestor mark. The image importer
copied the generation directly into the required wall-v9.png output path.
`finish_wall29.js` then extracted only pigment darker than the original rock
within [890,742,1003,845], excluding model-redrawn surrounding stone. That
bounded addition was composited onto the exact ancestor pixels. Feathered edges
make the pigment sit on the rock. Every pixel outside the box is unchanged.

The final PNG replaced the generated output at the same path and was also
saved as continuation wall.png. No draft picture, crop or contact sheet was
saved in the workspace. The only new distinct pictures are the whole final wall
and its required 512 px JPEG; the continuation PNG duplicates the final wall.

The required PNG is 1254 × 1254 RGB. The JPEG uses the existing vendored encoder,
512 px, quality 75. Both final pictures were opened. See VISUAL_REVIEW.md and
image-checks29.json for the observed result, limits and exact bytes/hashes.
