# Experimental PBRP Kansas build attempt

Not flash-tested. Owner variant and build are NOT confirmed. No flash or release publication performed.
Device tree basis: councilcj/android_device_motorola_kansas at 0accbd2cd8dddc393e9e9d0762a0e05a1163482c.
Reference-only firmware: XT2513V Tracfone W1VKS36H.9-12-9-8-3 Android 16 from the public Lolinet mirror.
Stock vendor_boot members were range-extracted, CRC-checked and parent-image MD5 matched flashfile.xml.
Stock reference has boot/vendor_boot/init_boot A/B partitions, header v4, F2FS userdata/metadata, dynamic logical system partitions.
This candidate preserves the stock platform ramdisk and DTB, adds a compiled recovery ramdisk fragment and excludes invented recovery/cache partitions.
Encryption, touch/display drivers, bootloader fragment selection and actual-device compatibility remain untested.
Do not flash to an unidentified or locked device; no installation instructions are provided.
PBRP stable documented manifest android-12.1 is used at current heads; synced revision manifest will be saved.
Original branches and default workflows are preserved. Only the isolated temporary branch is changed.

Packaging: unsigned vendor_boot v4 postprocessing orders platform/DLKM fragments before RECOVERY in both the physical ramdisk and table, preserving compressed fragment payloads, board IDs, DTB, bootconfig and header. This prevents the stock platform archive from overwriting compiled recovery when fragments are consumed in image/table order. Android permits bootloaders to choose a different order; this is not proof of Kansas bootloader behavior. The generic init_boot ramdisk loads last under the Android specification. No stock signed image is modified.

Postprocessing regression tests cover byte preservation, idempotence, rejection of signatures, malformed overlaps, truncation and wrong version. Runtime binary/UI/fstab inspection of the actual generated image remains mandatory.
Reference: https://source.android.com/docs/core/architecture/partitions/vendor-boot-partitions
