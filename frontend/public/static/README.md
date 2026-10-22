# Static UI images

`src/components/common/customImage.tsx` loads UI images (logos and toolbar icons listed in
`src/assets/customIconNames.tsx`) from `UMI_APP_STATIC_RESOURCE_BASE_URL` (default `/static`,
i.e. this folder). The original image set is not part of this release; place your own PNG/SVG
files here using the file names from `customIconNames.tsx`, or point the variable at another host.
