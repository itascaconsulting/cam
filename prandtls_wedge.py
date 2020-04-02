import itasca as it
it.command("python-reset-state false")
from itasca import zonearray as za
from itasca import gridpointarray as gpa
import numpy as np

cohesion_array = np.array({cohesion_array})
nz = 20

datafile_string = f"""
model new
fish automatic-create off
fish define setup(name)
    global solution = (2.0 + math.pi)
    global cohesion = zone.prop(zone.head,'cohesion')
    ; Find all gridpoints on footing and store them in a list
    global points = gp.list(gp.isgroup(::gp.list,name))
    local height = gp.pos.z(points(1)) ; Height of footing
    global topPoints = gp.list(gp.pos(::gp.list)->z==height) ; Gps at footing height
    topPoints = topPoints(~gp.isgroup(::topPoints,name)) ; Remove gps in footing
    local xnext = list.min(gp.pos(::topPoints)->x) ; Left most gp x pos NOT on footing
    global width = (3.0 + xnext) * 0.5 ; Adjusted width
end
;---------------------------------------------------------------------
; p_load : average footing pressure / c
; c_disp : magnitude of vertical displacement at footing center / a
;---------------------------------------------------------------------
fish define load
    local accum = list.sum(gp.force.unbal(::points)->z)
    global disp = -gp.disp.z(points(1))
    load = accum / (width * cohesion)
end
model large-strain off
; Create zones
zone create brick size 6 1 {nz} point 1 (3.0,0.0,0.0) ...
                              point 3 (0.0,0.0,10.0) ...
                              ratio 0.9 1.0 0.97
zone create brick size 20 1 {nz} point 0 (3.0,0.0,0.0) ...
                               point 1 (20.0,0.0,0.0) ...
                               point 3 (3.0,0.0,10.0) ...
                               ratio 1.08 1.0 0.97
; Assign constitutive model and properties
zone cmodel assign mohr-coulomb
zone property bulk 2.e8 shear 1.e8 cohesion 1.e5
zone property friction 0. dilation 0. tension 1.e10
; Assign group name to footing surface
zone face group 'Footing' range position-x 0 3 position-z 10
; Boundary Conditions
zone face apply velocity-normal 0.0 range position-x 0
zone face apply velocity-normal 0.0 range union position-y 0 position-y 1
zone face apply velocity (0,0,0) range union position-x 20 position-z 0
zone gridpoint fix velocity (0,0,-0.5e-5) range position-x 0 3 position-z 10
zone gridpoint free velocity-x range position-x 3 position-z 10
[setup('Footing')]
fish history load
fish history solution
fish history disp
model history mechanical ratio-local
"""

it.command(datafile_string)

z = za.pos().T[2]
gp_z_max = gpa.pos().T[2].max()
heights = list(set(z))
heights.sort()
layer_number = np.zeros(len(z))
for i, h in enumerate(heights[::-1]):
    layer_number[z==h] = i
za.set_extra(1, layer_number)

cohesion = za.prop_scalar("cohesion")
for i, c in enumerate(cohesion_array):
    cohesion[layer_number==i] = c
za.set_prop_scalar("cohesion", cohesion)

it.command("model cycle 50000")
it.command('history export 1 vs 3 file "tmp.txt" truncate')
disp, load = np.loadtxt("tmp.txt", skiprows=2).T
result=dict()
result["disp"] = disp.tolist()
result["load"] = load.tolist()
result["end_load"] = float(load[-1])
