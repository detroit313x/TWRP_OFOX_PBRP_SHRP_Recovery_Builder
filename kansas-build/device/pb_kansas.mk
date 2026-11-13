# Inherit from generic 64-bit configurations
$(call inherit-product, $(SRC_TARGET_DIR)/product/core_64_bit.mk)
$(call inherit-product, $(SRC_TARGET_DIR)/product/full_base_telephony.mk)

# Inherit from your local device.mk
$(call inherit-product, device/motorola/kansas/device.mk)

$(call inherit-product, vendor/pb/config/common.mk)

PRODUCT_DEVICE := kansas
PRODUCT_NAME := pb_kansas
PRODUCT_BRAND := motorola
PRODUCT_MODEL := Moto G 2025
PRODUCT_MANUFACTURER := motorola

BOARD_VENDOR := motorola
TARGET_VENDOR := motorola
