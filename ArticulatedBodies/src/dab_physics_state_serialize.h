/** \file dab_physics_state_serialize.h
*/

#pragma once

#include "dab_singleton.h"
#include "dab_exception.h"
#include "dab_value.h"
#include "dab_physics_state.h"
#include <map>

namespace dab
{

namespace physics
{

#pragma mark PresetPhysicsMap declaration
class PresetPhysicsMap
{
	public:
		PresetPhysicsMap(const std::string& pPresetParameterName, const std::string& pPhysicsParameterName, const AbstractValue& pPhysicsParameterValue);
		PresetPhysicsMap(const std::vector<std::string>& pPresetParameterNames, const std::string& pPhysicsParameterName, const AbstractValue& pPhysicsParameterValue);

		void update(const std::string& pPresetParameterName, const AbstractValue& pValue) throw (dab::Exception);

		const AbstractValue& physicsValue() const;

	protected:
		std::vector<std::string> mPresetParameterNames;
		std::string mPhysicsParameterName;
		std::shared_ptr<AbstractValue> mPhysicsParameterValue;
};

#pragma mark PresetPhysicsMaps declaration
class PresetPhysicsMaps
{
public:
	PresetPhysicsMaps(const std::string& pName);

	bool hasPresetName(const std::string& pPresetParameterName) const;
	bool hasPhysicsName(const std::string& pPhysicsParameterName) const;

	void addMap(const std::string& pPresetParameterName, const std::string& pPhysicsParameterName, const AbstractValue& pPhysicsParameterValue);
	void addMap(const std::vector<std::string>& pPresetParameterNames, const std::string& pPhysicsParameterName, const AbstractValue& pPhysicsParameterValue);

	void update(const std::string& pPresetParameterName, const AbstractValue& pValue) throw (dab::Exception);

	const AbstractValue& physicsValue(const std::string& pPhysicsParameterName) throw (dab::Exception);

protected:
	std::string mName;
	std::vector<std::shared_ptr<PresetPhysicsMap>> mMaps;
	std::map<std::string, std::shared_ptr<PresetPhysicsMap>> mPresetNameMap;
	std::map<std::string, std::shared_ptr<PresetPhysicsMap>> mPhysicsNameMap;
};

#pragma mark StateSerialize declaration
class StateSerialize : public Singleton<StateSerialize>
{
public:
	StateSerialize();

	void loadStateFromMaxPreset(State& pState, const std::string& pPresetFileName, int pPresetNr, const std::string& pPresetMapName) throw (dab::Exception);

	void addPresetPhysicsMap(const std::string& pMapName, const std::string& pPresetParameterName, const std::string& pPhysicsParameterName, const AbstractValue& pPhysicsParameterValue) throw (dab::Exception);
	void addPresetPhysicsMap(const std::string& pMapName, const std::vector<std::string>& pPresetParameterNames, const std::string& pPhysicsParameterName, const AbstractValue& pPhysicsParameterValue) throw (dab::Exception);


protected:
	std::map<std::string, std::shared_ptr<PresetPhysicsMaps>> mPresetPhysicsMaps;

	void init();
	void createDefaultMaps();
};

};

};