within FMI.FMI2.Functions;
impure function FMI2DoStep
  input Internal.ExternalFMU externalFMU;
    input Real currentCommunicationPoint;
    input Real communicationStepSize;
    input Boolean noSetFMUStatePriorToCurrentPoint;
    external"C" FMU_FMI2DoStep(externalFMU, currentCommunicationPoint, communicationStepSize, noSetFMUStatePriorToCurrentPoint) annotation (Library="ModelicaFMI");
  annotation ();
end FMI2DoStep;
