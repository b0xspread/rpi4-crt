# Raspberry Pi 4 and CRT

State of affairs:

## 1. Composite SDTV output is disabled by default and will slow your system down. 


> enable_tvout (Pi 4B only)
> On the Raspberry Pi 4, composite output is disabled by default, due to the way the internal clocks are interrelated and allocated. Because composite video requires a very specific clock, setting that clock to the required speed on the Pi 4 means that other clocks connected to it are detrimentally affected, which slightly slows down the entire system. Since composite video is a less commonly used function, we decided to disable it by default to prevent this system slowdown.
> 
> To enable composite output, use the enable_tvout=1 option. As described above, this will detrimentally affect performance to a small degree.
> 
> On older Pi models, the composite behaviour remains the same.

Source: https://www.raspberrypi.org/documentation/configuration/config-txt/video.md

Here are the settings I use on my 20" Trinitron.

```
framebuffer_width=580
framebuffer_height=360 
enable_tvout=1
sdtv_mode=0
sdtv_aspect=1
disable_overscan=1
audio_pwm_mode=2
```

## 2. You will need a correct 4-pole 3.5mm to A/V RCA cable. 
There are many similar cables out there bundled with various A/V equipment, however most of them have ground on PIN1 and won't work, **but the cable we need must have composite video on PIN1.** The wiring of the other pins doesn't matter. So for example if PIN1 on the 3.5mm jack is wired to the white or red RCA connector it will still work as video, you just plug that into the TV Composite port instead of the yellow connector. This is the cable I used and can verify that it works and has the correct wiring: https://www.adafruit.com/product/2881

I believe the following cable is also wired correctly: https://www.amazon.com/Gam3Gear-Composite-Cable-Microsoft-XBox-360/dp/B011KLLMR2

If you don't see the rainbow screen on your display, try power cycling.

## 3. Now using `sdtv_mode=0/2` you will be in 480i. 
I recommend you keep it that way as a boot default and Emulationstation. Try playing your favorite ROMs first, and you will probably notice that the interlace shake is rather annoying, and there may be other issues. In my experience Sakitoshi's `tvout_smart` and `tvout_sharp` shaders (https://github.com/Sakitoshi/retropie-crt-tvout/tree/master/to_configs/all/retroarch/shaders) do a great job of improving things quite a bit, but just make sure you **Shader #X Filter to Linear**. Try one of them as the only shader pass first. You may want to check out the configs in that repo as some platforms need additional tuning.


## 4. 240p - Background

You can boot directly into 240p by setting `sdtv_mode=16/18` for NTSC/PAL.

Mode switching between 480i and 240p via DRM/KMS is currently not possible.

Installing X11 and adding ModeLines using `xrandr` also won't work. You will essentially resize the framebuffer, but the output will remain the same. The TV output is controlled by the VEC DAC (encoder generating the analog PAL or NTSC composite signal), but the VEC is not accessible with the fake/firmware `vc4-fkms-v3d driver` and my understanding is the `vc4-kms-v3d-pi4` which would allow direct hardware access is still experimental. The following gives a good description of the different driver models: 

>FKMS (fake) uses the dispmanx and mailbox API's to talk to the firmware for things like the composition and video output stages.
>
>KMS does all that by accessing the HW registers directly from ARM space, bypassing the firmware completely.

>It's down to what actually drives the video scaler (HVS), pixel valves, and output display blocks (HDMI/VEC/DSI/DPI).
>With vc4-fkms-v3d this remains with the firmware, and the firmware still allows DispmanX or MMAL to add extra layers.
>With vc4-kms-v3d, the Linux kernel is driving all that lot, and DRM prohibits multiple clients adding layers at the same time.

Source: https://www.raspberrypi.org/forums/viewtopic.php?p=1507622#p1507247

**TV mode selection is done by an atomic property on the encoder, because a drm_mode_modeinfo is insufficient to distinguish between PAL and PAL-M or NTSC and NTSC-J.**

Source: https://dri.freedesktop.org/docs/drm/gpu/vc4.html

For example setting the default NTSC mode requires updating CONFIG0 and CONFIG1 registers, apart from the DRM modeline:
https://github.com/torvalds/linux/blob/master/drivers/gpu/drm/vc4/vc4_vec.c#L244
https://github.com/torvalds/linux/blob/master/drivers/gpu/drm/vc4/vc4_vec.c#L256
https://github.com/torvalds/linux/blob/master/drivers/gpu/drm/vc4/vc4_vec.c#L286

(example would apply in full KMS mode only)

In order to achieve 240p the following changes to the output signal are needed:

- Integer number of lines (either 262 or 263) instead of 262.5 (x2 = 525) used for interlacing
- This will cause the VSync pulse to be sent at the end of a scanline and not in the middle of it, thus the scanlines will be retraced instead of being shifted down due to the ramp restart of the electron beam sawtooth wave.
- Change to the VSync and equalization pulses within the CSync signal sent during the blanking period

Source: https://www.hdretrovision.com/blog/2018/10/22/engineering-csync-part-1-setting-the-stage


When we set a progressive mode in `config.txt` (`sdtv_mode=16/18`) the ***firmware*** does something similar to what the vc4_vec driver would do in full KMS mode:

A. Sets the progressive scan bit in the `VEC_CONFIG2` register of the VEC register set:
https://github.com/torvalds/linux/blob/master/drivers/gpu/drm/vc4/vc4_vec.c#L104

B. Removes the interlace flag for the mode:
https://github.com/torvalds/linux/blob/master/drivers/gpu/drm/vc4/vc4_vec.c#L260

There are probably other steps needed as well.

Source: https://github.com/raspberrypi/firmware/issues/683#issuecomment-283179792

`tvservice` essentially sends a VCHI message requesting the corresponding sdtv_mode from the firmware:

https://github.com/raspberrypi/userland/blob/2448644657e5fbfd82299416d218396ee1115ece/interface/vmcs_host/vc_sdtv.h#L60
https://github.com/raspberrypi/userland/blob/master/host_applications/linux/apps/tvservice/tvservice.c#L703
https://github.com/raspberrypi/userland/blob/master/interface/vmcs_host/vc_vchi_tvservice.c#L1213
https://github.com/raspberrypi/userland/blob/master/interface/vmcs_host/vc_vchi_tvservice.c#L698

The VEC in the new BCM2711 SoC is the same as in the older BCM2835 therefore the register regions remain valid:

```
 $ dtc -I dtb -O dts -o ~/devicetree.dts /boot/bcm2711-rpi-4-b.dtb
 $ grep "vec" ~/devicetree.dts 
		vec@7e806000 {
			compatible = "brcm,bcm2835-vec";
		vec = "/soc/vec@7e806000"; 
```



## 240p - How to make it work

The good news is 240p per ROM/Platform is still possible! Now granted it's not EXACTLY 240p since DRM/KMS doesn't recognize the changes we make with `tvservice`. The framebuffer still has a 480 line resolution, but the interlacing flicker is gone and the TV is outputting 240p on screen. On my 20" Sony Trinitron, NES games look perfect with only the `tvout_smart` or `tvout_sharp` shader applied, horizontal and vertical scrolling seems fine. 240p test suite includes a horizontal scroll test for various platforms: http://junkerhq.net/xrgb/index.php?title=240p_test_suite

If you aren't happy with the outcome, read this post as it has a lot of information on tweaking the output in 240p: https://retropie.org.uk/forum/topic/11628/240p-and-mame-scaling/12

### Mode Enforcement

Now the last problem to resolve is enforcing the output. Out of the box RetroPie comes with a KMS DRM modesetting mechanism that works like this:
- You set the desired mode in videomodes.cfg
- runcommand.sh injects the modeset environment variables for SDL2 modesetting
- retroarch starts and loads SDL2 which sees the environment variables and sets the mode

Unfortunately this doesnt work on RPi4, and thows us back into 480i, as it is the only mode defined. Attempting to set progressive scan with `tvservice` prior to retroarch launching will yield the same outcome. Our only solution is to wait for retroarch/SDL2 to finish loading and then switch back to progressive scan.

I put together a simple script `vmodes_watcher.py` that runs in the background and monitors the value of a desired_mode file. If the file is modified, it waits for `retroarch` to start and then changes the screen to the desired mode with `tvservice`.

to install it do the following

```
$ git clone git@github.com:b0xspread/rpi4-crt.git
$ cd rpi4-crt
$ cp runcommand-onend.sh  runcommand-onstart.sh  vmodes_watcher.py /opt/retropie/configs/all
$ mkdir /opt/retropie/configs/all/desired_mode
$ echo 'NTSC 4:3 P' > /opt/retropie/configs/all/desired_mode/value
$ sudo bash
# pip3 install watchdog psutil
# sed  "s/exit 0/su pi -c 'python3 -u \/opt\/retropie\/configs\/all\/vmodes_watcher.py &> \/var\/log\/vmodes_watcher.log' &\nexit 0/" /etc/rc.local
# reboot
```

To verify the watcher is running:

```
$ ps ax | grep vmodes_watcher.py$
  595 ?        Sl     0:00 python3 -u /opt/retropie/configs/all/vmodes_watcher.py
```

To monitor activity:

```
$ watch cat /var/log/vmodes_watcher.log
```


Now try playing a ROM from a platform with 240p support (ex. NES). If everything installed correctly you should no longer see the flicker. Apply those tvout shaders previously mentioned and see which one you like best.

If you were monitoring the log file you should see something like this:

```
Every 2.0s: cat /var/log/vmodes_watcher.log                                                                 retropie: Wed May 13 19:29:54 2020

Starting watcher...
Waiting for retroarch to start...
Waiting for retroarch to start...
Waiting for retroarch to start...
Waiting for retroarch to start...
Setting desired display mode: 'NTSC 4:3 P' ...
Powering on SDTV with explicit settings (mode:16 aspect:1)
```

When you exit, Emulationstation should be back to 480i (this can be changed in `runcommand-onend.sh`)

### Setting desired_mode per ROM/platform

240p is the default mode for `runcommand-onstart.sh`. In order to force 480i for a particular game or platform you need to add the rom name or `all` in the corresponding `480i.txt` file. 

For example if I want all MAME ROMs to run in 480i I would do the following:
```
cat /opt/retropie/configs/mame-libretro/480i.txt 
all
```

Alternatively if I just wanted a particular ROM to run in 480i I would do this instead:

```
cat /opt/retropie/configs/mame-libretro/480i.txt 
umk3.zip
```

## Shaders

Check out the following post for instructions on tweaking the image for 224/240p and the pi_iq_horz_nearest_vert shader:

https://retropie.org.uk/forum/topic/11628/240p-and-mame-scaling/12


Sakitoshi has a great repo containing shaders, configurations and palletes for various platforms:

https://github.com/Sakitoshi/retropie-crt-tvout


