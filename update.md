Remmmember your pervious mistakes and first analysze my Common app and /home/revdev/Desktop/Daily/Devalaya/PowerBank/ChargeGhar/Common.md file You need to analyzed my full project context regarding my {{app_name}} and you need figured out the gaps, inconsitency,, duplicacy , also you need to anylize and ensured what other parts of the common app we need to implement here — like caching and others — according to the situation? think from different aspects to use the common app properly, also by fixing what you analyzed.

your target should be:

1. analyze the gap between the current app and how the common app will be used according to the condition of the code implemented now

2. inconsistent serializer

3. use common app decorators for caching, logging, and see others if needed according to the scenario

---

**1. Inconsistent Serializer-View Mapping:**

* views return custom response formats that don't match `serializer_class`
* missing proper pagination serializers in Swagger
* some views don't use the common mixins properly

**2. Missing MVP Focus:**

* no distinction between list and detail serializers
* no real-time data considerations
* inconsistent response formats

---

at last, use the manual caching finder script in each app, and you can run it using:

```bash
python ./tools/find_cache_manual.py --<app_name>
```

after running it, update the services to remove manual caching since we're using decorators.

make sure it’s your handy tool.