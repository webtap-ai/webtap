# Guide to the define new Custom Taps

The following guide is about defining Custom Taps by extending the ApifyTap class and adding the custom logic in it.

## Steps

1. **Update Tap Manager**: In `data/tap_manager/tap_index.json`, create a JSON item 
```json
"tripadvisor_custom" : {
    "class_" : "webtap.taps.custom.{custom_tap_filename}.{custom_tap_classname}"
}` 
```
2. In taps/custom/ create a new file {custom_tap_filename}.py and define a class {custom_tap_classname} that extends ApifyTap