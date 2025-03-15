/** \file dab_physics_state.h
*/

#pragma once

#include "dab_value.h"
#include "dab_singleton.h"
#include "ofThread.h"
#include <map>

namespace dab
{

namespace physics
{

	class BodyPart;
	class BodyJoint;
	class BodyMotor;
	class Behavior;
	class StateTransition;
		
	// TODO: deal with group behavior effect

	enum StateEffectType
	{
		BodyPartEffect,
		BodyJointEffect,
		BodyMotorEffect,
		BodyBehaviorEffect
	};
			
	# pragma mark StateEffect declaration
	class StateEffect
	{
	public:
		StateEffect(StateEffectType pEffectType, const std::vector<std::string>& pBodyNames, const std::vector<std::string>& pTargetNames, const std::string& pParameterName, const AbstractValue& pParameterValue);
		StateEffect(const StateEffect& pStateEffect);

		const StateEffect& operator=(const StateEffect& pStateEffect);

		StateEffectType effectType() const;
		const std::vector<std::string>& bodyNames() const;
		const std::vector<std::string>& targetNames() const;
		const std::string& parameterName() const;
		const std::shared_ptr<AbstractValue> parameterValue() const;

		void changeBodies(const std::vector<std::string>& pBodyNames);
		void changeTargets(const std::vector<std::string>& pTargetNames);
		void changeParameterName(const std::string& pParameterName);
		void changeParameterValue(const AbstractValue& pParameterValue);

		void init() throw(dab::Exception);
		void apply() throw(dab::Exception);

		virtual operator std::string() const;

		virtual std::string info() const;

		friend std::ostream& operator<< (std::ostream& pOstream, const StateEffect& pStateEffect)
		{
			pOstream << pStateEffect.info();

			return pOstream;
		};
		
	protected:
		StateEffectType mEffectType;

		std::vector<std::string> mBodyNames;
		std::vector<std::string> mTargetNames;
		std::string mParameterName;

		std::shared_ptr<AbstractValue> mParameterValue;

		std::vector<std::shared_ptr<BodyPart>> mBodyParts;
		std::vector<std::shared_ptr<BodyJoint>> mBodyJoints;
		std::vector<std::shared_ptr<BodyMotor>> mBodyMotors;
		std::vector<std::shared_ptr<Behavior>> mBodyBehaviors;
		
		std::vector<std::shared_ptr<BodyPart>> gatherParts() throw (dab::Exception);
		std::vector<std::shared_ptr<BodyJoint>> gatherJoints() throw (dab::Exception);
		std::vector<std::shared_ptr<BodyMotor>> gatherMotors() throw (dab::Exception);
		std::vector<std::shared_ptr<Behavior>> gatherBehaviors() throw (dab::Exception);
	};

	# pragma mark State declaration
	class State
	{
	public:
		State(const std::string& pStateName);
		State(const State& pState);

		const State& operator=(const State& pState);

		const std::string& name() const;
		bool active() const;
		const std::vector<std::shared_ptr<StateEffect>>& stateEffects() const;
		std::shared_ptr<State> parentState() const;
		const std::vector<std::shared_ptr<State>>& subStates() const;

		void setStateName(const std::string& pStateName);
		void setActive(bool pActive, bool pIncludeSubStates = false);
		void addStateEffect(const StateEffect& pStateEffect);
		void addSubState(const State& pSubState); // makes copy of state
		void addSubState(std::shared_ptr<State>& pSubState); // doesn't make copy of state
		void setParentState(std::shared_ptr<State>& pParentState); 

		const std::vector<std::shared_ptr<StateTransition> >& incomingStateTransitions() const;
		const std::vector<std::shared_ptr<StateTransition> >& outgoingStateTransitions() const;
		void addIncomingStateTransition(std::shared_ptr<StateTransition> pTransition);
		void addOutgoingStateTransition(std::shared_ptr<StateTransition> pTransition);

		void changeBodies(const std::vector<std::string>& pBodyNames, bool pIncludeSubStates = false);
		void changeBodies(const std::vector<std::string>& pBodyNames, StateEffectType pEffectType, bool pIncludeSubStates = false);
		void changeBodies(const std::vector<std::string>& pBodyNames, StateEffectType pEffectType, const std::string& pParameterName, bool pIncludeSubStates = false);
		void changeTargets(const std::vector<std::string>& pTargetNames, bool pIncludeSubStates = false);
		void changeTargets(const std::vector<std::string>& pTargetNames, StateEffectType pEffectType, bool pIncludeSubStates = false);
		void changeTargets(const std::vector<std::string>& pTargetNames, StateEffectType pEffectType, const std::string& pParameterName, bool pIncludeSubStates = false);
		void changeParameterName(const std::string& pParameterName);
		void changeParameterValue(const std::string& pParameterName, const AbstractValue& pParameterValue, bool pIncludeSubStates = false);
		void changeParameterValue(const std::vector<std::string>& pTargetNames, const std::string& pParameterName, const AbstractValue& pParameterValue, bool pIncludeSubStates = false);

		void update() throw(dab::Exception);
		void apply() throw(dab::Exception);

		virtual operator std::string() const;

		virtual std::string info() const;

		friend std::ostream& operator<< (std::ostream& pOstream, const State& pState)
		{
			pOstream << pState.info();

			return pOstream;
		};

	protected:
		std::string mName;
		bool mActive;
		std::vector<std::shared_ptr<StateEffect>> mStateEffects;

		std::shared_ptr<State> mParentState;
		std::vector<std::shared_ptr<State>> mSubStates;

		std::vector<std::shared_ptr<StateTransition>> mIncomingStateTransitions;
		std::vector<std::shared_ptr<StateTransition>> mOutgoingStateTransitions;
	};

	# pragma mark StateTransitionCondition declaration
	class StateTransitionCondition
	{
	public:
		StateTransitionCondition();
		StateTransitionCondition(const StateTransitionCondition& pCondition);

		const StateTransitionCondition& operator=(const StateTransitionCondition& pCondition);
		virtual std::shared_ptr<StateTransitionCondition> copy() const;

		bool ready() const;
		void setReady(bool pReady);

		virtual void update();
		virtual void reset();


	protected:
		bool mReady;
	};

	# pragma mark StateTransitionTimed declaration

	class StateTransitionTimed : public StateTransitionCondition
	{
	public:
		StateTransitionTimed(double pDuration);
		StateTransitionTimed(const StateTransitionTimed& pCondition);

		const StateTransitionTimed& operator=(const StateTransitionTimed& pCondition);
		virtual std::shared_ptr<StateTransitionCondition> copy() const;

		virtual void update();
		virtual void reset();

	protected:
		double mResetTime;
		double mDuration;
	};

	# pragma mark StateTransition declaration

	class StateTransition
	{
	public:
		StateTransition(std::shared_ptr<State> pPreviousState, std::vector<std::shared_ptr<State>> pNextStates, const StateTransitionCondition& pCondition);

		void setProbabilities(const std::vector<float>& pProbabilties);

		bool ready();
		void update();
		void reset();
		std::shared_ptr<State> apply();

	protected:

		std::shared_ptr<State> mPreviousState;
		std::vector<std::shared_ptr<State>> mNextStates;
		std::vector<float> mNextStateProbabilities;
		std::shared_ptr<StateTransitionCondition> mTransitionCondition;
	};

	# pragma mark StateMachine declaration

	class StateMachine : public ofThread
	{
	public:
		StateMachine();

		void addState(std::shared_ptr<State> pState);

		void start();
		void stop();
		bool paused() const;
		void setPaused(bool pPaused);
		void update();

	protected:
		std::vector<std::shared_ptr<State> > mStates;
		bool mPaused;
		double mUpdateInterval;
		double mTime;

		void threadedFunction();
	};

	# pragma mark StateManager declaration

	class StateManager : public Singleton<StateManager>
	{
	public:
		StateManager();

		std::shared_ptr<State> state(const std::string& pStateName) const throw (dab::Exception);

		std::shared_ptr<State> createState(const std::string& pStateName) throw (dab::Exception);
		std::shared_ptr<State> loadState(const std::string& pStateName, const std::string& pPresetFileName, int pPresetNr, const std::string& pPresetMapName) throw (dab::Exception);
		std::shared_ptr<State> copyState(const std::string& pSourceStateName) throw (dab::Exception);
		std::shared_ptr<State> copyState(const std::string& pSourceStateName, const std::string& pTargetStateName) throw (dab::Exception);
		std::shared_ptr<State> addSubState(const std::string& pParentStateName, const std::string& pSubStateName) throw (dab::Exception);
		std::shared_ptr<StateTransition> createStateTransition(const std::string& pPreviousStateName, const std::vector<std::string>& pNextStateNames, const StateTransitionCondition& pCondition) throw (dab::Exception);

		std::shared_ptr<State> loadState(std::shared_ptr<State> pState, const std::string& pPresetFileName, int pPresetNr, const std::string& pPresetMapName) throw (dab::Exception);
		std::shared_ptr<State> copyState(std::shared_ptr<State> pSourceState);
		std::shared_ptr<State> addSubState(std::shared_ptr<State> pParentState, std::shared_ptr<State> pSubState);
		std::shared_ptr<StateTransition> createStateTransition(std::shared_ptr<State> pPreviousState, const std::vector<std::shared_ptr<State>>& pNextStates, const StateTransitionCondition& pCondition);


	protected:
		std::map< std::string, std::shared_ptr<State> > mStates;

		void init();
		void createDefaultStates();
	};
};

};