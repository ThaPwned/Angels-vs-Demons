import math

from mathlib import QAngle
from mathlib import Vector


def AngleVectors(angles):
    # TODO: Turns out, this math is not quite right (atleast for the IsInsideCone functions below)
    # sy, cy = SinCos(Deg2Rad(angles[0]))
    # sp, cp = SinCos(Deg2Rad(angles[1]))
    # sr, cr = SinCos(Deg2Rad(angles[2]))

    # forward = [cp * cy, cp * sy, -sp]
    # right = [-1 * sr * sp * cy + -1 * cr * -sy, -1 * sr * sp * sy + -1 * cr * cy, -1 * sr * cp]
    # up = [cr * sp * cy + -sr * -sy, cr * sp * sy + -sr * cy, cr * cp]

    # return forward, right, up

    angles = QAngle(*angles)
    forward = Vector()
    right = Vector()
    up = Vector()

    angles.get_angle_vectors(forward, right, up)

    return list(forward), list(right), list(up)


def SinCos(radians):
    return math.sin(radians), math.cos(radians)


def Deg2Rad(x):
    return x * (math.pi / 180)


def VectorAngles(vector):
    if not vector[1] and not vector[0]:
        yaw = 0

        if vector[2] > 0:
            pitch = 270
        else:
            pitch = 90
    else:
        yaw = Deg2Rad(math.atan2(vector[1], vector[0]))

        if yaw < 0:
            yaw += 360

        tmp = math.sqrt(vector[0] * vector[0] + vector[1] * vector[1])
        pitch = Deg2Rad(math.atan2(-vector[2], tmp))

        if pitch < 0:
            pitch += 360

    return pitch, yaw, 0


def InFront(origin, angles, offset=[64.0, 64.0, 64.0]):
    origin[0] = origin[0] + offset[0] * math.cos(Deg2Rad(0.0 - angles[0])) * math.cos(Deg2Rad(angles[1]))
    origin[1] = origin[1] + offset[1] * math.cos(Deg2Rad(0.0 - angles[0])) * math.sin(Deg2Rad(angles[1]))
    origin[2] = origin[2] + offset[2] * math.sin(Deg2Rad(0.0 - angles[0]))

    return origin


# https://forums.alliedmods.net/showpost.php?p=973411&postcount=4
# def IsInsideCone(player, target, max_distance=None, threshold=0.73):
#     # player, target = target, player
#     eye_location = player.eye_location
#     eye_angle = QAngle(*player.eye_angle)
#     target_eye_location = target.eye_location

#     distance = target_eye_location - eye_location
#     # distance = Vector()

#     # distance[0] = target_eye_location[0] - eye_location[0]
#     # distance[1] = target_eye_location[1] - eye_location[1]
#     # # distance[2] = target_eye_location[2] - eye_location[2]
#     # distance[2] = 0

#     print(distance)

#     if max_distance is not None:
#         if ((distance[0] ** 2) + (distance[1] ** 2)) > max_distance ** 2:
#             return False

#     eye_angle[2] = 0
#     # forward = Vector(*AngleVectors(eye_angle)[0])
#     forward = Vector()
#     right = Vector()
#     up = Vector()
#     eye_angle.get_angle_vectors(forward, right, up)

#     distance.normalize()

#     print(forward.dot(distance), threshold)

#     return forward.dot(distance) >= threshold

# stock bool:ClientViews(Viewer, Target, Float:fMaxDistance=0.0, Float:fThreshold=0.73)
# {
#     decl Float:fViewPos[3];   GetClientEyePosition(Viewer, fViewPos);
#     decl Float:fViewAng[3];   GetClientEyeAngles(Viewer, fViewAng);
#     decl Float:fViewDir[3];
#     decl Float:fTargetPos[3]; GetClientEyePosition(Target, fTargetPos);
#     decl Float:fTargetDir[3];
#     decl Float:fDistance[3];

#     fViewAng[0] = fViewAng[2] = 0.0;
#     GetAngleVectors(fViewAng, fViewDir, NULL_VECTOR, NULL_VECTOR);

#     fDistance[0] = fTargetPos[0]-fViewPos[0];
#     fDistance[1] = fTargetPos[1]-fViewPos[1];
#     fDistance[2] = 0.0;
#     if (fMaxDistance != 0.0)
#     {
#         if (((fDistance[0]*fDistance[0])+(fDistance[1]*fDistance[1])) >= (fMaxDistance*fMaxDistance))
#             return false;
#     }

#     NormalizeVector(fDistance, fTargetDir);
#     if (GetVectorDotProduct(fViewDir, fTargetDir) < fThreshold) return false;

#     new Handle:hTrace = TR_TraceRayFilterEx(fViewPos, fTargetPos, MASK_PLAYERSOLID_BRUSHONLY, RayType_EndPoint, ClientViewsFilter);
#     if (TR_DidHit(hTrace)) { CloseHandle(hTrace); return false; }
#     CloseHandle(hTrace);

#     return true;
# }

# public bool:ClientViewsFilter(Entity, Mask, any:Junk)
# {
#     if (Entity >= 1 && Entity <= MaxClients) return false;
#     return true;
# }


# https://forums.alliedmods.net/showpost.php?p=2240625&postcount=10
# def IsInsideCone(origin, angle, target_origin, max_distance=None, cone_angle=45):
#     if max_distance is not None:
#         if origin.get_distance_sqr(target_origin) > max_distance ** 2:
#             return False

#     forward = Vector(*AngleVectors(angle)[0])

#     diff = target_origin - origin

#     thisangle = math.acos(forward.dot(diff) / (forward.length * diff.length))
#     thisangle = thisangle * 360 / 2 / math.pi

#     return thisangle <= cone_angle

# stock bool:FindTargetInViewCone(iViewer, iTarget, Float:max_distance=0.0, Float:cone_angle=180.0) // 180.0 could be for backstabs and stuff
# {
#     if (IsValidClient(iViewer))
#     {
#         if(max_distance<0.0)    max_distance=0.0;
#         if(cone_angle<0.0)      cone_angle=0.0;

#         decl Float:PlayerEyePos[3];
#         decl Float:PlayerAimAngles[3];
#         decl Float:PlayerToTargetVec[3];

#         decl Float:OtherPlayerPos[3];
#         GetClientEyePosition(iViewer,PlayerEyePos);
#         GetClientEyeAngles(iViewer,PlayerAimAngles);

#         decl Float:ThisAngle;
#         decl Float:playerDistance;
#         decl Float:PlayerAimVector[3];

#         GetAngleVectors(PlayerAimAngles,PlayerAimVector,NULL_VECTOR,NULL_VECTOR);

#         if(IsValidClient(iTarget) && IsPlayerAlive(iTarget) && iViewer!=iTarget)
#         {
#             GetClientEyePosition(iTarget,OtherPlayerPos);

#             playerDistance = GetVectorDistance(PlayerEyePos,OtherPlayerPos);
#             if(max_distance>0.0 && playerDistance>max_distance)
#             {
#                 return false;
#             }
#             SubtractVectors(OtherPlayerPos,PlayerEyePos,PlayerToTargetVec);
#             ThisAngle=ArcCosine(GetVectorDotProduct(PlayerAimVector,PlayerToTargetVec)/(GetVectorLength(PlayerAimVector)*GetVectorLength(PlayerToTargetVec)));
#             ThisAngle=ThisAngle*360/2/3.14159265;
#             if(ThisAngle<=cone_angle)
#             {
#                 ignoreClient=iViewer;
#                 TR_TraceRayFilter(PlayerEyePos,OtherPlayerPos,MASK_ALL,RayType_EndPoint,AimTargetFilter);
#                 if(TR_DidHit())
#                 {
#                     new entity=TR_GetEntityIndex();
#                     if(entity!=iTarget)
#                     {
#                         return false;
#                     }
#                     else
#                     {
#                         return true;
#                     }
#                 }
#             }
#         }
#     }
#     return false;
# }

# new ignoreClient;
# public bool:AimTargetFilter(entity,contentsMask)
# {
#     return !(entity==ignoreClient);
# }


# TODO: Get a better name... ConeChecker... wtf?
class ConeChecker(object):
    def __init__(self, player, max_distance=None, cone_angle=45):
        self.max_distance = None if max_distance is None else max_distance ** 2
        self.cone_angle = cone_angle

        angles = QAngle(*player.eye_angle)
        forward = Vector()
        right = Vector()
        up = Vector()

        angles.get_angle_vectors(forward, right, up)

        self._forward = forward
        self._origin = player.eye_location

    def has_within(self, target):
        if self.max_distance is not None:
            if self._origin.get_distance_sqr(target) > self.max_distance:
                return False

        diff = target - self._origin

        thisangle = math.acos(self._forward.dot(diff) / (self._forward.length * diff.length))
        thisangle = thisangle * 360 / 2 / math.pi

        if thisangle > self.cone_angle:
            return False

        # TODO: Get some trace rays going
        return True
