#include "StdAfx.h"
#include "EngOborDic.h"
#pragma warning(disable:4786) 




COborDic* NewOborDicEnglish (CSyntaxOpt* Opt)
{
	return new CEngOborDic(Opt);
};

static const size_t CoordConjTypesCount = 5;
static const CCoordConjType CoordConjTypes[CoordConjTypesCount] = {
	{"AND", false},
	{"OR", false},
	{"BUT", false},
	{"YET", false},
	{"SO", false}
};

static const size_t SubConjTypesCount = 14;
static const std::string SubConjTypes[SubConjTypesCount] = {
	"BECAUSE", "BEFORE", "IF", "SINCE", "THAT", "THOUGH",
	"UNLESS", "UNTIL", "WHEN", "WHILE", "WHERE", "HOW",
	"WHETHER", "WHILST"
};

CEngOborDic::CEngOborDic(const CSyntaxOpt* Opt) : COborDic(Opt)
{
	m_SimpleCoordConj.clear();
	for (size_t i=0; i < CoordConjTypesCount;i++)
		m_SimpleCoordConj.push_back(CoordConjTypes[i]);

	m_SimpleSubConj.clear();
	for (size_t i=0; i < SubConjTypesCount;i++)
		m_SimpleSubConj.push_back(SubConjTypes[i]);
}

/*
static long GetItemNoByItemStr(const CDictionary* piOborDic, const char* ItemStr, const char* _DomStr) 
{
	BYTE DomNo = piOborDic->GetDomenNoByDomStr(_DomStr);
    return piOborDic->GetItemNoByItemStr(ItemStr, DomNo);
}
*/






bool CEngOborDic::ReadOborDic (const CDictionary* piOborDic)
{
	try
	{
		if(piOborDic == NULL )
			return false;

		m_SimpleSubConj.clear();
		
	}
	catch(...)
	{		
		return false;
	}
	return true; 	
};




