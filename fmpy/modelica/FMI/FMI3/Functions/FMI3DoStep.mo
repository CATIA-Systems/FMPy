within FMI.FMI3.Functions;
impure function FMI3DoStep
  input Internal.ExternalFMU externalFMU;
    input Real currentCommunicationPoint;
    input Real communicationStepSize;
    external"C" FMU_FMI3DoStep(externalFMU, currentCommunicationPoint, communicationStepSize) annotation (Library="ModelicaFMI");
  annotation ();
end FMI3DoStep;
