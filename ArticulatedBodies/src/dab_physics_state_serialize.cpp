/** \file dab_physics_state_serialize.cpp
*/

#include "dab_physics_state_serialize.h"
#include "dab_util_max_preset.h"
#include <array>

using namespace dab;
using namespace dab::physics;

#pragma mark PresetPhysicsMap definition

PresetPhysicsMap::PresetPhysicsMap(const std::string& pPresetParameterName, const std::string& pPhysicsParameterName, const AbstractValue& pPhysicsParameterValue)
	: mPresetParameterNames({ pPresetParameterName })
	, mPhysicsParameterName(pPhysicsParameterName)
	, mPhysicsParameterValue(pPhysicsParameterValue.copy())
{}

PresetPhysicsMap::PresetPhysicsMap(const std::vector<std::string>& pPresetParameterNames, const std::string& pPhysicsParameterName, const AbstractValue& pPhysicsParameterValue)
	: mPresetParameterNames(pPresetParameterNames)
	, mPhysicsParameterName(pPhysicsParameterName)
	, mPhysicsParameterValue(pPhysicsParameterValue.copy())
{}

const AbstractValue& 
PresetPhysicsMap::physicsValue() const
{
	return *mPhysicsParameterValue;
}

void 
PresetPhysicsMap::update(const std::string& pPresetParameterName, const AbstractValue& pValue) throw (dab::Exception)
{
	//std::cout << "PresetPhysicsMap::update PresetParameterName " << pPresetParameterName  << " pValue " << pValue << " ";

	try
	{
		std::vector<int> valueIndices;
		for (int i = 0; i < mPresetParameterNames.size(); ++i)
		{
			if (mPresetParameterNames[i] == pPresetParameterName) valueIndices.push_back(i);
		}
		if(valueIndices.size() == 0) throw dab::Exception("Physics Error: preset parameter name " + pPresetParameterName + " not found", __FILE__, __FUNCTION__, __LINE__);

		// super cumbersome assignment procedure from a one dimensional abstract value to a multi dimensional abstract value, check if this can be simplified
		if (mPhysicsParameterValue->type() == pValue.type())
		{
			*(mPhysicsParameterValue) = pValue;
		}
		else if (mPhysicsParameterValue->typeMatch<float>() && pValue.typeMatch<int>())
		{
			int tmp = pValue;
			mPhysicsParameterValue->set<float>(static_cast<float>(tmp));
		}
		else if (mPhysicsParameterValue->typeMatch<bool>() && pValue.typeMatch<int>())
		{
			int tmp = pValue;
			mPhysicsParameterValue->set<bool>(static_cast<bool>(tmp));
		}
		else if (mPhysicsParameterValue->dim() == 3)
		{
			if (mPhysicsParameterValue->typeMatch<std::array<float, 3>>() && pValue.typeMatch<float>())
			{
				for (int i = 0; i < valueIndices.size(); ++i)
				{
					(mPhysicsParameterValue->get<std::array<float, 3>>())[valueIndices[i]] = pValue;
				}
			}
			else if (mPhysicsParameterValue->typeMatch<std::array<int, 3>>() && pValue.typeMatch<int>())
			{
				for (int i = 0; i < valueIndices.size(); ++i)
				{
					(mPhysicsParameterValue->get<std::array<int, 3>>())[valueIndices[i]] = pValue;
				}
			}
			if (mPhysicsParameterValue->typeMatch<std::array<float, 3>>() && pValue.typeMatch<int>())
			{
				int tmp = pValue;

				for (int i = 0; i < valueIndices.size(); ++i)
				{
					(mPhysicsParameterValue->get<std::array<float, 3>>())[valueIndices[i]] = static_cast<float>(tmp);;
				}
			}
			else if (mPhysicsParameterValue->typeMatch<std::array<bool, 3>>() && pValue.typeMatch<int>())
			{
				int tmp = pValue;

				for (int i = 0; i < valueIndices.size(); ++i)
				{
					(mPhysicsParameterValue->get<std::array<bool, 3>>())[valueIndices[i]] = static_cast<bool>(tmp);
				}
			}
		}
	}
	catch (dab::Exception& e)
	{
		throw e;
	}

	//std::cout << " PhysicsParameterName " << mPhysicsParameterName << " value " << *mPhysicsParameterValue << "\n";
}

#pragma mark PresetPhysicsMaps definition

PresetPhysicsMaps::PresetPhysicsMaps(const std::string& pName)
	: mName(pName)
{}

bool 
PresetPhysicsMaps::hasPresetName(const std::string& pPresetParameterName) const
{
	return mPresetNameMap.find(pPresetParameterName) != mPresetNameMap.end();
}

bool 
PresetPhysicsMaps::hasPhysicsName(const std::string& pPhysicsParameterName) const
{
	return mPhysicsNameMap.find(pPhysicsParameterName) != mPhysicsNameMap.end();
}

void 
PresetPhysicsMaps::addMap(const std::string& pPresetParameterName, const std::string& pPhysicsParameterName, const AbstractValue& pPhysicsParameterValue)
{
	//std::cout << "PresetPhysicsMaps::addMap pPresetParameterName " << pPresetParameterName << " pPhysicsParameterName " << pPhysicsParameterName << " pPhysicsParameterValue " << pPhysicsParameterValue << "\n";

	if (mPresetNameMap.find(pPresetParameterName) != mPresetNameMap.end()) throw dab::Exception("Physics Error: preset parameter " + pPresetParameterName + " already added", __FILE__, __FUNCTION__, __LINE__);
	if (mPhysicsNameMap.find(pPhysicsParameterName) != mPhysicsNameMap.end()) throw dab::Exception("Physics Error: physics parameter " + pPhysicsParameterName + " already added", __FILE__, __FUNCTION__, __LINE__);

	std::shared_ptr<PresetPhysicsMap> _map( new PresetPhysicsMap(pPresetParameterName, pPhysicsParameterName, pPhysicsParameterValue));

	mMaps.push_back(_map);
	mPresetNameMap[pPresetParameterName] = _map;
	mPhysicsNameMap[pPhysicsParameterName] = _map;
}

void 
PresetPhysicsMaps::addMap(const std::vector<std::string>& pPresetParameterNames, const std::string& pPhysicsParameterName, const AbstractValue& pPhysicsParameterValue)
{
	for(int i=0; i< pPresetParameterNames.size(); ++i) if (mPresetNameMap.find(pPresetParameterNames[i]) != mPresetNameMap.end()) throw dab::Exception("Physics Error: preset parameter " + pPresetParameterNames[i] + " already added", __FILE__, __FUNCTION__, __LINE__);
	if (mPhysicsNameMap.find(pPhysicsParameterName) != mPhysicsNameMap.end()) throw dab::Exception("Physics Error: physics parameter " + pPhysicsParameterName + " already added", __FILE__, __FUNCTION__, __LINE__);

	std::shared_ptr<PresetPhysicsMap> _map(new PresetPhysicsMap(pPresetParameterNames, pPhysicsParameterName, pPhysicsParameterValue));

	mMaps.push_back(_map);
	for (int i = 0; i < pPresetParameterNames.size(); ++i) mPresetNameMap[pPresetParameterNames[i]] = _map;
	mPhysicsNameMap[pPhysicsParameterName] = _map;
}

void 
PresetPhysicsMaps::update(const std::string& pPresetParameterName, const AbstractValue& pValue) throw (dab::Exception)
{
	if (mPresetNameMap.find(pPresetParameterName) == mPresetNameMap.end()) return;

	try
	{
		mPresetNameMap[pPresetParameterName]->update(pPresetParameterName, pValue);
	}
	catch(dab::Exception& e)
	{
		throw e;
	}
}

const AbstractValue& 
PresetPhysicsMaps::physicsValue(const std::string& pPhysicsParameterName) throw (dab::Exception)
{
	if (mPhysicsNameMap.find(pPhysicsParameterName) == mPhysicsNameMap.end()) throw dab::Exception("Physics Error: physics parameter name " + pPhysicsParameterName + " not found", __FILE__, __FUNCTION__, __LINE__);

	return mPhysicsNameMap[pPhysicsParameterName]->physicsValue();
}

#pragma mark StateSerialize definition


StateSerialize::StateSerialize()
{
	init();
}

void
StateSerialize::loadStateFromMaxPreset(State& pState, const std::string& pPresetFileName, int pPresetNr, const std::string& pPresetMapName) throw (dab::Exception)
{
	//std::cout << "StateSerialize::loadStateFromMaxPreset pPresetFileName " << pPresetFileName << " pPresetNr " << pPresetNr << " " << pPresetMapName << "\n";

	try
	{
		if (mPresetPhysicsMaps.find(pPresetMapName) == mPresetPhysicsMaps.end()) throw dab::Exception("Physics Error: preset map " + pPresetMapName + " not found", __FILE__, __FUNCTION__, __LINE__);

		std::shared_ptr<util::MaxPreset> maxPreset = util::MaxPresetLoader::get().loadPreset(pPresetFileName, pPresetNr);
		std::shared_ptr<PresetPhysicsMaps> presetMap = mPresetPhysicsMaps[pPresetMapName];

		const std::map<std::string, std::shared_ptr<AbstractValue>>& maxPresetValues = maxPreset->namedValues();
		for (auto iter : maxPresetValues)
		{
			//std::cout << "update preset parameter " << iter.first << "\n";

			if (presetMap->hasPresetName(iter.first))
			{
				presetMap->update(iter.first, *(iter.second));
			}
		}

		const std::vector<std::shared_ptr<StateEffect>>& stateEffects = pState.stateEffects();
		for (auto stateEffect : stateEffects)
		{
			const std::string& physicsParameterName = stateEffect->parameterName();

			//std::cout << "update physics parameter " << physicsParameterName << "\n";

			if (presetMap->hasPhysicsName(physicsParameterName))
			{
				const AbstractValue& physicsParameterValue = presetMap->physicsValue(physicsParameterName);
				stateEffect->changeParameterValue(physicsParameterValue);
			}
		}
	}
	catch (dab::Exception& e)
	{
		throw e;
	}
}

void 
StateSerialize::addPresetPhysicsMap(const std::string& pMapName, const std::string& pPresetParameterName, const std::string& pPhysicsParameterName, const AbstractValue& pPhysicsParameterValue) throw (dab::Exception)
{
	if (mPresetPhysicsMaps.find(pMapName) == mPresetPhysicsMaps.end())
	{
		std::shared_ptr<PresetPhysicsMaps> _map( new PresetPhysicsMaps(pMapName));
		mPresetPhysicsMaps[pMapName] = _map;
	}

	try
	{
		mPresetPhysicsMaps[pMapName]->addMap(pPresetParameterName, pPhysicsParameterName, pPhysicsParameterValue);
	}
	catch (dab::Exception& e)
	{
		throw e;
	}
}

void 
StateSerialize::addPresetPhysicsMap(const std::string& pMapName, const std::vector<std::string>& pPresetParameterNames, const std::string& pPhysicsParameterName, const AbstractValue& pPhysicsParameterValue) throw (dab::Exception)
{
	if (mPresetPhysicsMaps.find(pMapName) == mPresetPhysicsMaps.end())
	{
		std::shared_ptr<PresetPhysicsMaps> _map(new PresetPhysicsMaps(pMapName));
		mPresetPhysicsMaps[pMapName] = _map;
	}

	try
	{
		mPresetPhysicsMaps[pMapName]->addMap(pPresetParameterNames, pPhysicsParameterName, pPhysicsParameterValue);
	}
	catch (dab::Exception& e)
	{
		throw e;
	}
}

void
StateSerialize::init()
{
	createDefaultMaps();
}

void 
StateSerialize::createDefaultMaps()
{
	// create maps between max/msp presets and simulation parameters

	// create Physics map
	addPresetPhysicsMap("Physics", "partMass", "mass", dab::Value<float>(0.0));
	addPresetPhysicsMap("Physics", "partLinearDamping", "linearDamping", dab::Value<float>(0.0));
	addPresetPhysicsMap("Physics", "partAngularDamping", "angularDamping", dab::Value<float>(0.0));
	addPresetPhysicsMap("Physics", "partFriction", "friction", dab::Value<float>(0.0));
	addPresetPhysicsMap("Physics", "partRollingFriction", "rollingFriction", dab::Value<float>(0.0));
	addPresetPhysicsMap("Physics", "partRestitution", "restitution", dab::Value<float>(0.0));
	addPresetPhysicsMap("Physics", "motorBounce", "bounce", dab::Value<float>(0.0));
	addPresetPhysicsMap("Physics", "motorDamping", "damping", dab::Value<float>(0.0));
	addPresetPhysicsMap("Physics", { "motorAngularActive_XY", "motorAngularActive_XY", "motorAngularActive_Z" }, "angularActive", dab::Value<std::array<bool, 3>>({ false, false, false }));
	addPresetPhysicsMap("Physics", { "jointAngularLowerLimit_XY", "jointAngularLowerLimit_XY", "jointAngularLowerLimit_Z" }, "angularLowerLimit", dab::Value<std::array<float, 3>>({ 0.0, 0.0, 0.0 }));
	addPresetPhysicsMap("Physics", { "jointAngularUpperLimit_XY", "jointAngularUpperLimit_XY", "jointAngularUpperLimit_Z" }, "angularUpperLimit", dab::Value<std::array<float, 3>>({ 0.0, 0.0, 0.0 }));
	addPresetPhysicsMap("Physics", { "jointAngularStopERP_XY", "jointAngularStopERP_XY", "jointAngularStopERP_Z" }, "angularStopERP", dab::Value<std::array<float, 3>>({ 0.0, 0.0, 0.0 }));
	addPresetPhysicsMap("Physics", { "jointAngularStopCFM_XY", "jointAngularStopCFM_XY", "jointAngularStopCFM_Z" }, "angularStopCFM", dab::Value<std::array<float, 3>>({ 0.0, 0.0, 0.0 }));
	addPresetPhysicsMap("Physics", { "motorMaxAngularForce_XY", "motorMaxAngularForce_XY", "motorMaxAngularForce_Z" }, "maxAngularMotorForce", dab::Value<std::array<float, 3>>({ 0.0, 0.0, 0.0 }));
	addPresetPhysicsMap("Physics", { "motorAngularVelocity_XY", "motorAngularVelocity_XY", "motorAngularVelocity_Z" }, "angularVelocity", dab::Value<std::array<float, 3>>({ 0.0, 0.0, 0.0 }));
	addPresetPhysicsMap("Physics", { "servoAngularActive_XY", "servoAngularActive_XY", "servoAngularActive_Z" }, "angularServoActive", dab::Value<std::array<bool, 3>>({ false, false, false }));
	addPresetPhysicsMap("Physics", { "servoAngularPosition_XY", "servoAngularPosition_XY", "servoAngularPosition_Z" }, "angularServoTarget", dab::Value<std::array<float, 3>>({ 0.0, 0.0, 0.0 }));
	addPresetPhysicsMap("Physics", { "springAngularActive_XY", "springAngularActive_XY", "springAngularActive_Z" }, "angularSpringActive", dab::Value<std::array<bool, 3>>({ false, false, false }));
	addPresetPhysicsMap("Physics", { "springAngularStiffness_XY", "springAngularStiffness_XY", "springAngularStiffness_Z" }, "angularSpringStiffness", dab::Value<std::array<float, 3>>({ 0.0, 0.0, 0.0 }));
	addPresetPhysicsMap("Physics", { "springAngularDamping_XY", "springAngularDamping_XY", "springAngularDamping_Z" }, "angularSpringDamping", dab::Value<std::array<float, 3>>({ 0.0, 0.0, 0.0 }));
	addPresetPhysicsMap("Physics", { "springAngularTarget_XY", "springAngularTarget_XY", "springAngularTarget_Z" }, "angularSpringRestLength", dab::Value<std::array<float, 3>>({ 0.0, 0.0, 0.0 }));
	
	// create speed behavior map
	addPresetPhysicsMap("SpeedBehavior", "Speed_target", "speed", dab::Value<float>(0.0));
	addPresetPhysicsMap("SpeedBehavior", "Speed_amount", "amount", dab::Value<float>(0.0));

	// create target attraction behavior map
	addPresetPhysicsMap("TargetAttractionBehavior", { "TargetAttraction_targetPosX", "TargetAttraction_targetPosY", "TargetAttraction_targetPosZ" }, "targetPos", dab::Value<std::array<float, 3>>({ 0.0, 0.0, 0.0 }));
	addPresetPhysicsMap("TargetAttractionBehavior", "TargetAttraction_minDist", "minDist", dab::Value<float>(0.0));
	addPresetPhysicsMap("TargetAttractionBehavior", "TargetAttraction_maxDist", "maxDist", dab::Value<float>(10.0));
	addPresetPhysicsMap("TargetAttractionBehavior", "TargetAttraction_minAmp", "minAmp", dab::Value<float>(0.0));
	addPresetPhysicsMap("TargetAttractionBehavior", "TargetAttraction_maxAmp", "maxAmp", dab::Value<float>(10.0));
	addPresetPhysicsMap("TargetAttractionBehavior", "TargetAttraction_appInterval", "appInterval", dab::Value<float>(1.0));

	// create RandomForceBehavior map
	addPresetPhysicsMap("RandomForceBehavior", { "RandomForce_minDir_x", "RandomForce_minDir_y", "RandomForce_minDir_z" }, "minDir", dab::Value<std::array<float, 3>>({ 0.0, 0.0, 0.0 }));
	addPresetPhysicsMap("RandomForceBehavior", { "RandomForce_maxDir_x", "RandomForce_maxDir_y", "RandomForce_maxDir_z" }, "maxDir", dab::Value<std::array<float, 3>>({ 0.0, 0.0, 0.0 }));
	addPresetPhysicsMap("RandomForceBehavior", "RandomForce_minAmp", "minAmp", dab::Value<float>(0.0));
	addPresetPhysicsMap("RandomForceBehavior", "RandomForce_maxAmp", "maxAmp", dab::Value<float>(0.0));
	addPresetPhysicsMap("RandomForceBehavior", "RandomForce_appInterval", "appInterval", dab::Value<float>(1.0));
	addPresetPhysicsMap("RandomForceBehavior", "RandomForce_changeInterval", "randInterval", dab::Value<float>(1.0));

	// create RandomTorqueBehavior map
	addPresetPhysicsMap("RandomTorqueBehavior", { "RandomTorque_minTorque_x", "RandomRotTarget_minTorque_y", "RandomRotTarget_minTorque_z" }, "minTorque", dab::Value<std::array<float, 3>>({ 0.0, 0.0, 0.0 }));
	addPresetPhysicsMap("RandomTorqueBehavior", { "RandomTorque_maxTorque_x", "RandomRotTarget_maxTorque_y", "RandomRotTarget_maxTorque_z" }, "maxTorque", dab::Value<std::array<float, 3>>({ 0.0, 0.0, 0.0 }));
	addPresetPhysicsMap("RandomTorqueBehavior", "RandomTorque_scale", "scale", dab::Value<float>(0.0));
	addPresetPhysicsMap("RandomTorqueBehavior", "RandomTorque_appInterval", "appInterval", dab::Value<float>(1.0));
	addPresetPhysicsMap("RandomTorqueBehavior", "RandomTorque_changeInterval", "randInterval", dab::Value<float>(1.0));

	// create RandomRotationTargetBehavior map
	addPresetPhysicsMap("RandomRotationTargetBehavior", { "RandomRotTarget_minTarget_x", "RandomRotTarget_minTarget_y", "RandomRotTarget_minTarget_z" }, "minTarget", dab::Value<std::array<float, 3>>({ 0.0, 0.0, 0.0 }));
	addPresetPhysicsMap("RandomRotationTargetBehavior", { "RandomRotTarget_maxTarget_x", "RandomRotTarget_maxTarget_y", "RandomRotTarget_maxTarget_z" }, "maxTarget", dab::Value<std::array<float, 3>>({ 0.0, 0.0, 0.0 }));
	addPresetPhysicsMap("RandomRotationTargetBehavior", "RandomRotTarget_speed", "speed", dab::Value<float>(0.0));
	addPresetPhysicsMap("RandomRotationTargetBehavior", "RandomRotTarget_appInterval", "appInterval", dab::Value<float>(1.0));
	addPresetPhysicsMap("RandomRotationTargetBehavior", "RandomRotTarget_changeInterval", "randInterval", dab::Value<float>(1.0));

	// create VolumeBehavior map
	addPresetPhysicsMap("VolumeBehavior", "Volume_maxDist", "maxDist", dab::Value<float>(10.0));
	addPresetPhysicsMap("VolumeBehavior", "Volume_minAmp", "minAmp", dab::Value<float>(0.0));
	addPresetPhysicsMap("VolumeBehavior", "Volume_maxAmp", "maxAmp", dab::Value<float>(1.0));
	addPresetPhysicsMap("VolumeBehavior", "Volume_appInterval", "appInterval", dab::Value<float>(1.0));

	// create CohesionBehavior map
	addPresetPhysicsMap("CohesionBehavior", "Cohesion_minDist", "minDist", dab::Value<float>(0.0));
	addPresetPhysicsMap("CohesionBehavior", "Cohesion_maxDist", "maxDist", dab::Value<float>(10.0));
	addPresetPhysicsMap("CohesionBehavior", "Cohesion_amount", "amount", dab::Value<float>(0.0));

	// create AlignmentBehavior map
	addPresetPhysicsMap("AlignmentBehavior", "Alignment_minDist", "minDist", dab::Value<float>(0.0));
	addPresetPhysicsMap("AlignmentBehavior", "Alignment_maxDist", "maxDist", dab::Value<float>(10.0));
	addPresetPhysicsMap("AlignmentBehavior", "Alignment_linearAmount", "linearAmount", dab::Value<float>(0.0));
	addPresetPhysicsMap("AlignmentBehavior", "Alignment_angularAmount", "angularAmount", dab::Value<float>(0.0));
	addPresetPhysicsMap("AlignmentBehavior", "Alignment_amount", "amount", dab::Value<float>(0.0));
}