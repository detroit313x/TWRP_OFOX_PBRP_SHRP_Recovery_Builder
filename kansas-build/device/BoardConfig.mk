#
# Copyright (C) 2026 The Android Open Source Project
#
# SPDX-License-Identifier: Apache-2.0
#

DEVICE_PATH := device/motorola/kansas

# For building with minimal manifest
ALLOW_MISSING_DEPENDENCIES := true

# Architecture
TARGET_ARCH := arm64
TARGET_ARCH_VARIANT := armv8-a
TARGET_CPU_ABI := arm64-v8a
TARGET_CPU_VARIANT := generic
TARGET_2ND_ARCH := arm
TARGET_2ND_ARCH_VARIANT := armv7-a-neon
TARGET_2ND_CPU_ABI := armeabi-v7a

# Bootloader
TARGET_BOOTLOADER_BOARD_NAME := kansas
TARGET_NO_BOOTLOADER := true

# --- THE "STABLE GRAPHICS" FIX ---
DEVICE_SCREEN_WIDTH := 720
DEVICE_SCREEN_HEIGHT := 1604
TARGET_SCREEN_DENSITY := 280

# MediaTek Kernel 5.15+ Display Settings
RECOVERY_GRAPHICS_FORCE_USE_LINUX_FB := true
TW_NO_UI := false
TW_RECOVERY_BUTTONS := true

# --- BUTTONS & INPUT ---
BOARD_HAS_NO_SELECT_BUTTON := false
TW_INPUT_BLACKLIST := "hbtp_vm,fts_ts"

# Experimental vendor_boot v4 target, derived from XT2513V reference firmware.
# The owner's exact variant/build remains unconfirmed. This is NOT flash-tested.
BOARD_BOOTIMG_HEADER_VERSION := 4
BOARD_KERNEL_PAGESIZE := 4096
BOARD_KERNEL_BASE := 0x40000000
BOARD_RAMDISK_OFFSET := 0x26f00000
BOARD_TAGS_OFFSET := 0x07c80000
BOARD_DTB_OFFSET := 0x07c80000
BOARD_MKBOOTIMG_ARGS := --header_version 4 --ramdisk_offset $(BOARD_RAMDISK_OFFSET) --tags_offset $(BOARD_TAGS_OFFSET) --dtb_offset $(BOARD_DTB_OFFSET)
TARGET_NO_KERNEL := true
BOARD_INCLUDE_DTB_IN_BOOTIMG := true
BOARD_PREBUILT_DTB := $(DEVICE_PATH)/dtb
BOARD_KERNEL_CMDLINE := bootopt=64S3,32N2,64N2 mem.enable_mglru=1 loglevel=4 initcall_debug=0
TARGET_BOARD_PLATFORM := mt6835
BOARD_FLASH_BLOCK_SIZE := 131072
BOARD_VENDOR_BOOTIMAGE_PARTITION_SIZE := 67108864
BOARD_MOVE_RECOVERY_RESOURCES_TO_VENDOR_BOOT := true
BOARD_INCLUDE_RECOVERY_RAMDISK_IN_VENDOR_BOOT := true
BOARD_VENDOR_RAMDISK_FRAGMENTS := platform
BOARD_VENDOR_RAMDISK_FRAGMENT.platform.PREBUILT := $(DEVICE_PATH)/stock_platform_ramdisk.lz4
BOARD_VENDOR_RAMDISK_FRAGMENT.platform.MKBOOTIMG_ARGS := --ramdisk_type PLATFORM
BOARD_USES_GENERIC_KERNEL_IMAGE := true
BOARD_USES_METADATA_PARTITION := true
BOARD_SUPER_PARTITION_SIZE := 0
TARGET_COPY_OUT_VENDOR := vendor
AB_OTA_UPDATER := true
AB_OTA_PARTITIONS += boot vendor_boot init_boot dtbo vbmeta vbmeta_system
TARGET_RECOVERY_FSTAB := $(DEVICE_PATH)/recovery.fstab
TW_THEME := portrait_hdpi
TW_INCLUDE_REPACKTOOLS := true
TW_INCLUDE_FASTBOOTD := true
# Encryption on Android 16/MediaTek is not established; do not advertise decryption.
TW_INCLUDE_CRYPTO := false
TW_NO_SCREEN_BLANK := true
