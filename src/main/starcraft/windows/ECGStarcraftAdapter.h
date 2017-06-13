#pragma once
#include <BWAPI.h>
#include "rapidjson/document.h"
#include "rapidjson/writer.h"
#include "rapidjson/stringbuffer.h"
#include "TransportBridge.h"

// Remember not to use "Broodwar" in any global class constructor!

class ECGStarcraftAdapter : public BWAPI::AIModule
{
public:
  // Virtual functions for callbacks, leave these as they are.
  virtual void onStart();
  virtual void onEnd(bool isWinner);
  virtual void onFrame();
  virtual void onSendText(std::string text);
  virtual void onReceiveText(BWAPI::Player player, std::string text);
  virtual void onPlayerLeft(BWAPI::Player player);
  virtual void onNukeDetect(BWAPI::Position target);
  virtual void onUnitDiscover(BWAPI::Unit unit);
  virtual void onUnitEvade(BWAPI::Unit unit);
  virtual void onUnitShow(BWAPI::Unit unit);
  virtual void onUnitHide(BWAPI::Unit unit);
  virtual void onUnitCreate(BWAPI::Unit unit);
  virtual void onUnitDestroy(BWAPI::Unit unit);
  virtual void onUnitMorph(BWAPI::Unit unit);
  virtual void onUnitRenegade(BWAPI::Unit unit);
  virtual void onSaveGame(std::string gameName);
  virtual void onUnitComplete(BWAPI::Unit unit);
  // Everything below this line is safe to modify.
private:
  TransportBridge* bridge;
  rapidjson::Document* message;
  rapidjson::Document* ntuple;
  rapidjson::StringBuffer* response;
  rapidjson::Writer<rapidjson::StringBuffer>* responseWriter;
  bool isDataSet = false;

  bool readMessage();
  bool sendMessage();
  bool ECGStarcraftAdapter::setResponse(const std::string key, const std::string value);
  bool ECGStarcraftAdapter::setResponse(const std::string key, const int value);
  bool ECGStarcraftAdapter::build(const BWAPI::UnitType unitType, int count);
  bool ECGStarcraftAdapter::gather(const BWAPI::UnitType resourceType);
  BWAPI::UnitType ECGStarcraftAdapter::getUnitType(const std::string unitName);
/*
  bool validateUnit(Unit unit);
  bool buildUnit(string type, unit actors);
  int buildUnits(string type, count, unit actors);
*/
};